"""
run_stage3 — Stage 3: decide, then fill when planable.

Stages 1–2 (Voice, Describe) live in llm_roles/. This module is the
boss: decide() (ASK / SUGGEST / PLAN), then a fill call for horizons
when planable, then when/calendar when a real duration span exists.

Does NOT auto-mint plan["progression"] children on PLAN — the user
steers the WHAT map via + / Paste / Suggest (see
docs/goal-to-project-migration.md A2). Legacy plan["steps"] / PLAN_KEYS
may still run beside an empty progression.

Clarification is not a separate LLM step in front of Decide - it is
one possible outcome of decide().
"""

from backend.foundation.time import resolve_duration
from backend.store.data_persistence import get_user
from backend.project.engine.judgment.decide import decide
from backend.project.engine.judgment.ask import ask
from backend.project.engine.judgment.prompts import FILL_SYSTEM_PROMPT
from backend.project.engine.judgment.shape import (
    PLAN_KEYS,
    _horizon_scope_instruction,
)
from backend.project.engine.judgment.current_time import current_time
from backend.project.engine.when.calendar import generate_structure

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
    sim_user_id: int | None,
    prior_suggestion: str | None,
    reply: str | None,
) -> str:
    """Grounding lines for the fill call - same context as Decide, plus
    which horizons to fill. No opening/decide instructions."""
    user_content = f"The current date and time is: {current_time()}\n\nMy goal is: {goal}"
    if sim_user_id is not None:
        vision = get_user(sim_user_id)
        if vision is not None:
            user_content += (
                f"\n\nThis project is part of a broader direction: "
                f"{vision['text']}"
            )
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


def run_stage3(
    goal: str, duration: str | None = None, sim_user_id: int | None = None,
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

    `sim_user_id`, `prior_suggestion`/`reply`, and `opening` match the
    previous combined-call contract - see decide.py for opening text
    and route_note() for how prior suggestion + reply are used.
    """
    decision = decide(
        goal,
        duration=duration,
        sim_user_id=sim_user_id,
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
    filled = ask(
        FILL_SYSTEM_PROMPT,
        _fill_user_content(goal, duration, sim_user_id, prior_suggestion, reply),
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
            # Legacy calendar fill can fail soft; WHAT map is user-steered.
            plan["steps"] = None

    # No auto-mint of progression children — user fills the middle
    # (+ / Paste / Suggest / chat-grounded suggest). construct_first_map
    # remains available for those paths; not called here (migration A2).
    return plan


# Older name — same function (planner / lifecycle still say generate_plan).
generate_plan = run_stage3


def _planability(plan: dict) -> str:
    """
    Named verdict on a run_stage3()/generate_plan()-shaped dict: "ask", "suggest",
    or "planable". Not a fourth model call - reads fields Decide (and
    opening enforcement) already set. create_goal() only distinguishes
    planable from everything else; route_note() tells suggest kinds apart.
    """
    if plan.get("clarification"):
        return "ask"
    if plan.get("suggested_duration") or plan.get("suggested_action"):
        return "suggest"
    return "planable"
