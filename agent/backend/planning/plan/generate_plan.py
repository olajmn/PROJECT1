"""
Stage 3 orchestration — decide, then fill when planable.

Conversation Stages 1–2 (Voice, Describe) live in llm_roles/. This
module is Planning's Stage 3 path: decide() (ASK / SUGGEST / PLAN),
then a separate fill call for horizons when planable, then
generate_structure() when a real duration span exists.

Also attaches plan["progression"] (shadow WHAT Step tree) when
planable — see construct_progression.py. Active still reads
plan["steps"] / PLAN_KEYS; progression is persisted beside them.

Clarification is not a separate LLM step in front of Decide - it is
one possible outcome of decide().
"""

from backend.foundation.time import resolve_duration
from backend.infrastructure.data_persistence import get_vision
from backend.planning.plan.construct_progression import construct_progression
from backend.planning.plan.decide import decide
from backend.planning.plan.json_request import ask_model
from backend.planning.plan.plan_prompts import FILL_SYSTEM_PROMPT
from backend.planning.plan.plan_schema import (
    PLAN_KEYS,
    _horizon_scope_instruction,
    _now_str,
)
from backend.planning.plan.plan_structure import generate_structure

# create_goal()'s first mint cannot land on an Action. Used when
# opening=True and Decide still returned suggested_action with nothing
# else to hold the turn.
OPENING_CLARIFICATION = (
    "This project needs a clearer end — what would 'far enough for now' "
    "look like?"
)


def _empty_horizons() -> dict:
    return {key: None for key in PLAN_KEYS}


def _reject_opening_action(plan: dict) -> dict:
    """Strip an Action off an opening mint. Timeframe is optional —
    missing duration must not force a clarification or wipe a
    planable Decide/Fill result. If the only thing left after
    clearing suggested_action is emptiness (pre-fill SUGGEST with no
    ASK), ask what done looks like."""
    had_action = bool(plan.get("suggested_action"))
    plan["suggested_action"] = None
    if plan.get("clarification") or plan.get("suggested_duration"):
        return plan
    # Decide already said PLAN (all nulls), or Fill already wrote
    # horizons — leave planable. Co-build does not wait on a span.
    if any(plan.get(key) for key in PLAN_KEYS):
        return plan
    if not had_action:
        return plan
    plan["clarification"] = OPENING_CLARIFICATION
    plan["now"] = None
    for key in PLAN_KEYS:
        plan[key] = None
    return plan


def _fill_user_content(
    goal: str,
    duration: str | None,
    vision_id: int | None,
    prior_suggestion: str | None,
    reply: str | None,
) -> str:
    """Grounding lines for the fill call - same context as Decide, plus
    which horizons to fill. No opening/decide instructions."""
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if vision_id is not None:
        vision = get_vision(vision_id)
        if vision is not None:
            user_content += f"\n\nThis goal is part of a broader direction: {vision['text']}"
    if prior_suggestion:
        user_content += (
            f"\n\nYou previously suggested this as a possible first step, "
            f"before the user replied: \"{prior_suggestion}\""
        )
        if reply:
            user_content += (
                f"\n\nThe user's reply to that suggestion: {reply}\n\n"
                "Read the reply in light of what you just suggested - it may accept it, "
                "correct or add to your understanding of the goal, or propose something "
                "else of their own, rather than being an unrelated restatement of the goal."
            )
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    else:
        user_content += "\n\nNo timeframe was given for this goal."
    user_content += _horizon_scope_instruction(duration)
    return user_content


def generate_plan(
    goal: str, duration: str | None = None, vision_id: int | None = None,
    prior_suggestion: str | None = None, reply: str | None = None,
    opening: bool = False,
) -> dict:
    """
    Takes a goal (a text string) and returns a dict with keys:
    clarification, suggested_duration, suggested_action, year, month,
    week, today, hour, minute, now, steps.

    Stage 3 Decide runs first (see decide.py). If that verdict is ASK
    or SUGGEST, horizons stay null and nothing is filled. If PLAN,
    a second model call fills the horizons; when `duration` resolves
    to a real span, generate_structure() attaches steps.

    `clarification` is a single question when the goal is too vague to
    plan - callers MUST check it first. `suggested_duration` /
    `suggested_action` are SUGGEST outcomes (see docs/planning-model.md
    § Minimum planability / ASK vs. SUGGEST). Mutual exclusion is
    enforced here in code after Decide returns.

    `vision_id`, `prior_suggestion`/`reply`, and `opening` match the
    previous combined-call contract - see decide.py for opening text
    and route_note() for how prior suggestion + reply are used.
    """
    decision = decide(
        goal,
        duration=duration,
        vision_id=vision_id,
        prior_suggestion=prior_suggestion,
        reply=reply,
        opening=opening,
    )

    plan = {
        **_empty_horizons(),
        "clarification": decision.get("clarification"),
        "suggested_action": decision.get("suggested_action"),
        "suggested_duration": decision.get("suggested_duration"),
        "steps": None,
        "progression": None,
    }

    if duration or not isinstance(plan.get("suggested_duration"), (str, type(None))):
        plan["suggested_duration"] = None
    if not isinstance(plan.get("suggested_action"), (str, type(None))):
        plan["suggested_action"] = None
    if not isinstance(plan.get("clarification"), (str, type(None))):
        plan["clarification"] = None

    if opening and not duration:
        plan = _reject_opening_action(plan)

    if plan.get("clarification"):
        plan["suggested_duration"] = None
        plan["suggested_action"] = None
        return plan
    if plan.get("suggested_action"):
        plan["suggested_duration"] = None
        return plan
    if plan.get("suggested_duration"):
        return plan

    # PLAN — second call fills horizons only.
    filled = ask_model(
        FILL_SYSTEM_PROMPT,
        _fill_user_content(goal, duration, vision_id, prior_suggestion, reply),
        PLAN_KEYS,
    )
    for key in PLAN_KEYS:
        plan[key] = filled.get(key)

    if opening and not duration:
        plan = _reject_opening_action(plan)
        if plan.get("clarification") or plan.get("suggested_duration"):
            return plan

    if duration:
        try:
            result = generate_structure(goal, duration, plan.get("now") or goal)
            if result is not None:
                plan["steps"] = result["steps"]
        except ValueError:
            # Legacy calendar fill can fail soft; shadow WHAT still runs.
            plan["steps"] = None

    # Shadow WHAT tree — count is progression judgment, not week candles.
    # Failure leaves progression None; legacy steps/now still stand.
    plan["progression"] = construct_progression(
        goal,
        right_now=plan.get("now"),
        duration=duration,
    )
    return plan


def _planability(plan: dict) -> str:
    """
    Named verdict on a generate_plan()-shaped dict: "ask", "suggest",
    or "planable". Not a fourth model call - reads fields Decide (and
    opening enforcement) already set. create_goal() only distinguishes
    planable from everything else; route_note() tells suggest kinds apart.
    """
    if plan.get("clarification"):
        return "ask"
    if plan.get("suggested_duration") or plan.get("suggested_action"):
        return "suggest"
    return "planable"
