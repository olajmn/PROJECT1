"""
Planner
=======

Goal -> structured Plan, via a local LLM (Ollama). Produces a plan
across seven time horizons and revises it based on feedback, and owns
the decisions around creating a goal and reacting to feedback on one -
persisted via infrastructure/data_persistence.py's save_plan(), not
reimplemented here. Never talks to the model directly (see
model_client.py/step_generator.py).

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

PLAN_KEYS stays in this module rather than with the helpers that split
out into their own files - it's genuine Plan shape, passed INTO
ask_model() as a parameter rather than read by it directly, so keeping
it here avoids a circular import. See docs/06-development.md for this
file's naming/reorganization history.

Run from the PROJECT ROOT: .venv/bin/python -m backend.goals.plan.planner
"""

# Contents
#  1. Plan schema
#      - PLAN_KEYS
#
#  2. Model prompts
#      - SYSTEM_PROMPT
#      - REPLAN_SYSTEM_PROMPT
#
#  3. Time helpers
#      - _now_str()
#      - _horizon_scope_instruction()
#      - frozen_duration_for()
#
#  4. Plan generation
#      - generate_plan()
#
#  5. Goal creation
#      - create_goal()
#
#  6. Replanning
#      - replan()
#      - apply_new_duration()
#
#  7. Feedback & step handling
#      - apply_feedback()
#      - advance_step()
#
#  8. Vision management
#      - set_goal_vision()
#      - archive_vision()
#
#  9. Cancellation
#      - cancel_goal()
#
#  10. CLI entry point
#      (module execution block; no named function)

from backend.foundation.time import (
    broadest_relevant_horizon,
    extract_duration_phrase,
    freeze_duration,
    now,
    resolve_duration,
    step_count,
)
from backend.goals.feedback.acknowledger import acknowledge
from backend.goals.feedback.feedback_parser import parse_outcome, requests_duration_change
from backend.goals.goal.resolver import get_history_for_goal, get_latest_for_all_goals, get_latest_for_goal
from backend.infrastructure.data_persistence import archive_vision as archive_vision_record, get_vision, save_plan, save_vision
from backend.goals.plan.model_client import ask_model
from backend.goals.plan.step_generator import generate_steps

# ============================================================
# 1. Plan schema
# ============================================================

# Defined once. ask_model() validates the LLM's response has exactly
# these keys (passed in by generate_plan()/replan() below); the
# templates (via frontend/app.py) iterate this same list to render
# every horizon in order.
PLAN_KEYS = (
    "year", 
    "month", 
    "week", 
    "today", 
    "hour", 
    "minute", 
    "now"
)

# ============================================================
# 2. Model prompts
# ============================================================

SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time, and the user's goal. They may also tell you roughly "
    "how long they want this plan to span (e.g. '30 minutes', 'this "
    "week', '3 months'). Ground everything in the real date/time you "
    "were given - never invent specifics (names, numbers, progress) the "
    "user didn't tell you.\n\n"
    "First, decide whether the goal as given is specific enough to plan "
    "at all. A bare noun or verb with no object or context (e.g. "
    "'read', 'run', 'work', with nothing else said) isn't - answering it "
    "would mean inventing what book, what distance, what task, none of "
    "which the user actually told you. If so, do NOT invent an answer: "
    "set clarification to ONE short question that would make the goal "
    "specific enough to plan, and set every one of "
    "year/month/week/today/hour/minute/now "
    "to JSON null.\n\n"
    "Otherwise, set clarification to JSON null. The plan has seven "
    "horizons, from broadest to narrowest: year, month, "
    "week, today, hour, minute, now - but not "
    "every goal's real timeframe reaches all the way up to year. "
    "You will be told exactly which of these horizons to FILL IN and "
    "which to leave as JSON null, based on the goal's actual given "
    "timeframe - respect that list exactly. Do NOT invent a value for "
    "any horizon you were told to leave null, even a plausible-sounding "
    "one - a goal given '3 months' has no honest year-horizon answer, "
    "inventing one anyway is fabrication, not planning. For every "
    "horizon you WERE told to fill in, give a concrete, realistic "
    "value, framed as how this goal connects to or fits within that "
    "time window (e.g. a habit it's part of, a pattern it continues, "
    "what stays true at that goal's own outer horizon, what's realistic "
    "to finish today, within this one hour, within this one minute).\n"
    "- 'now' is different from the horizons above it: not a time "
    "window description, but the actual trigger - the single most "
    "immediate, concrete action the user can take this very moment, "
    "small enough to start in the next 5 minutes. Always filled in, "
    "never one of the ones left null.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly these "
    "eight keys - clarification, year, month, week, today, "
    "hour, minute, now - each either a string value or "
    "JSON null as described above.\n"
)

REPLAN_SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time. The user already has a plan for their goal and is "
    "now giving you feedback on whether they completed the most "
    "immediate action ('now'). You will also see this goal's "
    "full history: every 'now' action tried so far, oldest first, "
    "each with the feedback that followed it - not just the single "
    "most recent step. Adjust the plan based on the latest feedback:\n"
    "- If they did NOT complete it, look at the history first. If "
    "'now' has already been made smaller one or more times without "
    "being completed, do NOT shrink it again - repeatedly shrinking the "
    "same preparatory step is not real progress, and there is no value "
    "in an action smaller than a few minutes. Instead, either directly "
    "address a concrete obstacle they named, or move the action toward "
    "actually attempting the core thing the goal itself names (e.g. if "
    "the goal is 'send 4 applications' and 'now' has only ever been "
    "research/browsing, the next 'now' should be to actually send "
    "one application, even in the smallest real form - not more "
    "research). Only make 'now' smaller the FIRST time it isn't "
    "completed, when the history shows no earlier shrink already "
    "happened.\n"
    "- If they DID complete it, move on to the next logical step.\n\n"
    "Ground everything in the real date/time you were given - never "
    "invent specifics (names, numbers, progress) the user didn't tell "
    "you.\n\n"
    "You will be told exactly which horizons should have a concrete "
    "value and which should be JSON null, same as the previous plan - "
    "this doesn't change on a replan just because the goal's scope "
    "grew in conversation. Never invent a value for a horizon named as "
    "null. Update whichever of the horizons you ARE filling in the "
    "feedback affects; carry the others forward unchanged if the "
    "feedback doesn't touch them.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly the "
    "same keys as before: year, month, week, today, "
    "hour, minute, now - each either a string value or "
    "JSON null.\n"
)


# ============================================================
# 3. Time helpers
# ============================================================


def _now_str() -> str:
    """Grounds the model's "right now" in the real current moment - it has no other sense of time."""
    return now().strftime("%A, %Y-%m-%d %H:%M")


def _horizon_scope_instruction(duration: str | None) -> str:
    """
    The "fill these horizons in, leave these as null" line, shared by
    generate_plan() and replan() so both compute the boundary the same
    way (see frozen_duration.py §3). `now` is always included in
    fill_keys - it's always the last/narrowest PLAN_KEYS entry, never
    the broadest relevant horizon itself.

    PLAN_KEYS[0] ("year") is a level name, not a literal duration - it
    has no broader horizon above it, so it's the one slot a goal's real
    length can exceed - a 5-year goal is just as "broadest relevant" as
    a 10-month one (see _HORIZON_LENGTH_THRESHOLDS), but the two need
    very different content. When PLAN_KEYS[0] is the broadest, the
    instruction names the goal's own actual resolved span instead of
    leaving the model to assume a literal year (SYSTEM_PROMPT's framing
    example talks about "that goal's own outer horizon" for the same
    reason).
    """
    broadest = broadest_relevant_horizon(duration)
    start = PLAN_KEYS.index(broadest)
    fill_keys = PLAN_KEYS[start:]
    null_keys = PLAN_KEYS[:start]
    instruction = f"\n\nFill in these horizons: {', '.join(fill_keys)}."
    if null_keys:
        instruction += f" Leave these horizons as JSON null: {', '.join(null_keys)}."
    if broadest == PLAN_KEYS[0]:
        instruction += (
            f" This goal's own actual outer timeframe is {resolve_duration(duration)} - "
            f"describe the '{PLAN_KEYS[0]}' horizon around that real timeframe, not "
            "literally one calendar year, whenever it's longer or shorter than that."
        )
    return instruction


def frozen_duration_for(plan: dict, duration: str | None) -> dict | None:
    """
    The frozen_duration to save alongside `plan` - None while `plan` is
    a clarification (nothing has actually started yet, so there's no
    honest countdown to freeze), otherwise freeze_duration(duration).
    Shared by generate_plan()'s and replan()'s callers (frontend/app.py)
    so this rule is expressed once instead of repeated at every call
    site that saves a plan.
    """
    return None if plan.get("clarification") else freeze_duration(duration)


# ============================================================
# 4. Plan generation
# ============================================================


def generate_plan(goal: str, duration: str | None = None) -> dict:
    """
    Takes a goal (a text string) and asks the local model to produce a
    structured plan, grounded in the real current date/time. `duration`
    is optional free text from the user (e.g. "30 minutes", "this
    week") describing how far ahead this plan should reach - no fixed
    choices, whatever the user types is passed straight through.
    Returns a dict with keys: clarification, year, month,
    week, now, steps.

    `clarification` (added 2026-08-21) is a single question (string)
    instead of a real plan when the goal as given is too vague to plan
    at all - e.g. a bare noun/verb like "read", with no object or
    context (see SYSTEM_PROMPT). Every other key is JSON null in that
    case; callers MUST check `clarification` first and, if it's set,
    treat this as "ask the user again", not as a plan to save - there's
    nothing real in the rest of the dict to act on yet.

    `steps` (added 2026-08-21) is a list of short step descriptions
    only when `duration` actually resolves to a real span (see
    frozen_duration.py §4 - Step planning) - None otherwise (no
    duration given, or free text that isn't grounded in a real span, or
    a clarification question came back instead of a plan). There's
    nothing honest to break into steps without a real timeframe to
    divide - same reasoning DEADLINE_RE's ungrounded deadlines already
    follow elsewhere in this project.

    Does NOT take a `vision_id`/Vision text yet - it's stored
    (data_persistence.save_plan()'s `vision_id`) but not supplied to
    the model here. If/when it is, a caller would resolve it to text
    and add one line to `user_content` below, same as `duration` (see
    docs/03-architecture.md § Vision).
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    plan = ask_model(SYSTEM_PROMPT, user_content, PLAN_KEYS + ("clarification",))

    plan["steps"] = None
    if plan.get("clarification"):
        return plan
    if duration:
        count = step_count(duration)
        if count is not None:
            plan["steps"] = generate_steps(goal, plan.get("now") or goal, count)
    return plan


# ============================================================
# 5. Goal creation
# ============================================================


def create_goal(typed_text: str, new_vision_text: str, vision_id_value: str) -> dict:
    """
    Generate a fresh plan for a new goal and save it. `typed_text`,
    `new_vision_text`, and `vision_id_value` are already read/stripped
    by the caller.

    One text field, not a separate goal/duration pair -
    `extract_duration_phrase()` searches the whole typed text for a
    recognized time phrase (e.g. "clean the apartment this weekend").
    If nothing recognized turns up, that's treated as "no timeframe
    given" DETERMINISTICALLY, before calling the model - same
    "code decides, model is just told" reasoning as
    _horizon_scope_instruction() (see docs/05-decisions.md, 2026-08-23).

    Only ever starts a NEW goal (mints its own goal_id via save_plan());
    extending an EXISTING goal's timeframe goes through
    apply_feedback()'s requests_duration_change() branch instead.

    `frozen_duration` is left None when generate_plan() comes back with
    `clarification` set (goal too vague in CONTENT to plan at all) -
    nothing has actually started yet, so there's no honest countdown to
    draw until apply_feedback() resolves the clarification into a real
    plan. Frozen for real only once that happens.

    `new_vision_text` is checked before `vision_id_value` - typing a
    new Vision always wins over whatever the select had chosen.
    Neither is required; carried forward unchanged on every later
    replan for this goal (a goal's vision doesn't change just because
    its plan does).
    """
    if new_vision_text:
        vision_id = save_vision(new_vision_text)["id"]
    elif vision_id_value:
        vision_id = int(vision_id_value)
    else:
        vision_id = None

    duration = extract_duration_phrase(typed_text)
    if duration is None:
        # Ask, deterministically, without a model call. Every other
        # horizon stays null, matching a content-vagueness
        # clarification's shape (see generate_plan()'s docstring).
        clarification_plan = {key: None for key in PLAN_KEYS}
        clarification_plan["clarification"] = "When do you want to do this, or how long should it take?"
        clarification_plan["steps"] = None
        return save_plan(typed_text, clarification_plan, duration=None, frozen_duration=None, vision_id=vision_id)
    plan = generate_plan(typed_text, duration)
    return save_plan(
        typed_text, plan, duration=duration,
        frozen_duration=frozen_duration_for(plan, duration),
        vision_id=vision_id,
    )


# ============================================================
# 6. Replanning
# ============================================================


def replan(goal: str, history: list[dict], feedback: str, duration: str | None = None) -> dict:
    """
    Takes the goal, its full history (oldest first), and feedback on
    the most recent "now" action, and asks the model for an
    updated plan. Returns the same shape as generate_plan().

    Passing the *whole* history, not just the previous plan, is what
    lets REPLAN_SYSTEM_PROMPT's "don't shrink 'now' more than once"
    rule work - a model shown only the last step can't notice it has
    already made the same task smaller several times in a row (see
    docs/06-development.md, 2026-08-20, for the drift this fixed).

    Same Vision note as generate_plan() above: not supplied here either yet.
    """
    # Named history_lines, not "steps" - unrelated to this file's
    # `steps` plan field/step_generator.generate_steps() (added later
    # the same day); this is prose lines for the replan prompt, not
    # the step list.
    history_lines = []
    for record in history:
        right_now = record["plan"].get("now") or "(none)"
        if record.get("feedback"):
            history_lines.append(f'- now: "{right_now}" -> feedback: "{record["feedback"]}"')
        else:
            history_lines.append(f'- now: "{right_now}" (the first plan, no feedback yet)')
    history_text = "\n".join(history_lines)

    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My goal is: {goal}\n\n"
        f"This goal's full history so far, oldest first:\n{history_text}\n\n"
        f"My feedback on the most recent 'now' action: {feedback}"
    )
    if duration:
        user_content += f"\n\nThis plan should still span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    return ask_model(REPLAN_SYSTEM_PROMPT, user_content, PLAN_KEYS)


def apply_new_duration(existing: dict, duration: str, feedback: str) -> dict:
    """
    Regenerate `existing`'s plan around a new duration span - the
    shared logic behind /feedback's conversational
    requests_duration_change() flow.

    Always calls generate_plan() again rather than patching
    duration/frozen_duration onto the existing record: changing the
    timeframe is a real new planning decision (new horizons, a new
    step list), not a countdown edit. `existing["vision_id"]` is
    carried forward unchanged, same as `goal_id` - a changed duration
    doesn't change which Vision the goal belongs to.
    """
    plan = generate_plan(existing["goal"], duration)
    return save_plan(
        existing["goal"], plan, feedback=feedback, duration=duration, goal_id=existing["goal_id"],
        frozen_duration=frozen_duration_for(plan, duration),
        vision_id=existing.get("vision_id"),
    )


# ============================================================
# 7. Feedback & step handling
# ============================================================


def apply_feedback(latest: dict, note: str) -> dict:
    """
    Classify the free-text note into an outcome (parse_outcome() - no
    LLM, recognized phrases only) and act on it. The note itself is the
    only signal - no separate "outcome" field (see docs/05-decisions.md,
    2026-08-20, for why, and why this never lets an LLM decide true/false).

    Before that, two earlier checks can take over the note entirely
    instead of treating it as a progress report:
    - `plan.clarification` set -> the note ANSWERS a pending question
      about the goal itself (see that branch below).
    - `plan.pending_duration_question` set -> the note answers "how
      long do you want this to run now?" (see apply_new_duration()).
    - otherwise, `requests_duration_change(note)` -> the note is a NEW
      request to change the timeframe (e.g. "can we change timeframe"),
      not a status report; applies immediately if a new duration is
      ALSO already in this same message (e.g. "change timeframe to 1
      hour"), otherwise asks the follow-up question and lets the
      pending_duration_question branch above catch the answer on the
      NEXT message. The goal's own conversation box is the only way to
      do this - there's no separate "extend timeframe" control on the
      card.

    `note` is already read and stripped by the caller (frontend/app.py's
    feedback()). Which goal this applies to is `latest` itself - the
    caller resolves it from the form's `goal_id` (each active goal's
    card posts its own), not "whatever was touched most recently
    overall". With more than one active goal shown at once, that
    distinction is the difference between feedback landing on the goal
    you actually meant versus a different one entirely.

    A cancelled goal (see cancel_goal()) is a no-op here - returns
    `latest` unchanged rather than risking a save_plan() call that
    doesn't carry `cancelled` forward, which would silently revive it.
    """
    if latest.get("cancelled"):
        return latest

    duration = latest.get("duration")

    if latest["plan"].get("clarification"):
        # No real plan yet - `note` answers the clarifying question, not
        # a status report. Routed through generate_plan() (not replan(),
        # built around `now` completion; not parse_outcome(), which
        # would force an answer like "speed and comprehension" through
        # outcome categories that don't apply).
        #
        # Joins every prior answer, not just this note (same reasoning
        # as replan()'s full-history pass) - a multi-round clarification
        # needs all answers together, or the next call re-asks what's
        # already covered. Safe here: this branch only runs while
        # `clarification` keeps recurring, so every past `feedback` in
        # this goal's history is a prior answer.
        prior_answers = [r["feedback"] for r in get_history_for_goal(latest["goal_id"]) if r.get("feedback")]
        combined_goal = " - ".join([latest["goal"], *prior_answers, note])
        # `duration` can still be None here specifically when this
        # clarification IS create_goal()'s missing-timeframe question -
        # the answer is a duration phrase, not more goal content, so it
        # needs the same extraction create_goal() does, or it stays
        # lost as untyped prose. Skipped when duration is already known
        # (a content-vagueness clarification) - `note` there answers a
        # different question, not a timeframe to (mis)parse.
        if duration is None:
            duration = extract_duration_phrase(note)
        plan = generate_plan(combined_goal, duration)
        # frozen_duration stays None for as long as clarification keeps
        # coming back (same reasoning as create_goal() above: nothing
        # has actually started yet) - only frozen for real, for the
        # first time, the moment a real plan finally comes back.
        return save_plan(
            latest["goal"], plan, feedback=note, duration=duration,
            goal_id=latest["goal_id"],
            frozen_duration=frozen_duration_for(plan, duration),
            vision_id=latest.get("vision_id"),
        )

    if latest["plan"].get("pending_duration_question"):
        # The PREVIOUS record asked "how long do you want this to run
        # now?" - this note is the answer, not a status report. Falls
        # back to the existing duration if nothing recognized - never
        # silently wipes a working timeframe.
        new_duration = extract_duration_phrase(note) or duration
        return apply_new_duration(latest, new_duration, feedback=note)

    if requests_duration_change(note):
        # A request to change the TIMEFRAME, not a progress report -
        # checked before parse_outcome() so it's never misread as one of
        # its outcomes (see requests_duration_change()'s docstring).
        # Applies immediately if the new duration is already IN this
        # message (e.g. "change timeframe to 1 hour"); only asks the
        # follow-up when nothing recognized turns up.
        new_duration = extract_duration_phrase(note)
        if new_duration:
            return apply_new_duration(latest, new_duration, feedback=note)

        # Carries the current plan/duration/steps forward completely
        # unchanged (this goal isn't being replanned or checked in on
        # right now) - only difference from a plain "carry forward"
        # save is the pending_duration_question flag, which is what
        # makes the branch above fire on the NEXT message and is what
        # active_goal/_conversation.html's thread shows as the agent's reply
        # instead of the real `now`.
        return save_plan(
            latest["goal"],
            {**latest["plan"], "pending_duration_question": "How long do you want this to run now?"},
            feedback=note, duration=duration, goal_id=latest["goal_id"],
            frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
            vision_id=latest.get("vision_id"),
        )

    # Inherited unchanged, never recomputed - a check-in isn't a new
    # planning decision, it's the SAME timeframe continuing (see
    # frozen_duration.py §1). Falls back to computing one fresh only
    # for a goal saved before frozen_duration existed - a one-time
    # "adopt now", not a recurring recompute.
    frozen = latest.get("frozen_duration") or freeze_duration(duration)
    classified = parse_outcome(note)
    # Anything not confidently recognized defaults to the same safe
    # no-op as "action_in_progress" - check in without changing the
    # plan, rather than guess toward a riskier outcome
    # (action_completed/goal_completed) from ambiguous text. See
    # parse_outcome()'s docstring.
    outcome_value = classified or "action_in_progress"

    if outcome_value == "goal_completed":
        # The whole goal is done, not just this one "now" step -
        # nothing left to plan, so no replan() call. Keep the existing
        # plan content, just mark this record as the completed one.
        feedback_text = "Marked the whole goal as complete." + (f" Note: {note}" if note else "")
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, completed=True, goal_id=latest["goal_id"],
            frozen_duration=frozen, vision_id=latest.get("vision_id"),
        )

    if outcome_value == "action_in_progress":
        # Mid-task, not stalled or failed - a distinct signal from "No"
        # (see docs/06-development.md, 2026-08-20, for the plan-drift
        # bug this fixed). No replan() call: check in without asking
        # the model to change anything. `classified` distinguishes "you
        # said you're still working on it" from "we couldn't tell" -
        # both get the same safe treatment, but the record stays honest
        # about which happened. The "couldn't tell" case asks the model
        # for a natural acknowledgment of `note` (acknowledge() -
        # display text only, can never change this branch or fail it).
        prefix = "Still working on it." if classified else acknowledge(note)
        feedback_text = prefix + (f" Note: {note}" if note else "")
        return save_plan(
            latest["goal"], latest["plan"], feedback=feedback_text,
            duration=duration, goal_id=latest["goal_id"], frozen_duration=frozen,
            vision_id=latest.get("vision_id"),
        )

    outcome = "Completed the action" if outcome_value == "action_completed" else "Did not complete the action"
    feedback_text = f"{outcome}." + (f" Note: {note}" if note else "")

    # The full chain, not just latest["plan"] - see replan()'s docstring
    # for why: a model only shown the single previous step has no way to
    # notice it has already shrunk `now` several times in a row.
    new_plan = replan(latest["goal"], get_history_for_goal(latest["goal_id"]), feedback_text, duration=duration)
    # goal_id carried forward explicitly - without this, save_plan() would
    # mint a fresh one and this replan would silently start a *new*
    # goal entry instead of continuing the existing goal's chain.
    return save_plan(
        latest["goal"], new_plan, feedback=feedback_text, duration=duration,
        goal_id=latest["goal_id"], frozen_duration=frozen, vision_id=latest.get("vision_id"),
    )


def advance_step(latest: dict, done: bool) -> dict:
    """
    Advances `current_step` by one - pure index arithmetic into the
    goal's already-generated `plan.steps` list, no model call (the step
    list was fully decided upfront by step_generator.generate_steps()).

    `done=False` doesn't move the pointer - logged the same safe,
    no-replan way as apply_feedback()'s "in_progress".

    `current_step` can reach `len(steps)` (one past the last valid
    index) to mean "every step is done" - not an automatic goal
    completion, just what active_goal/_task.html uses to prompt marking
    the whole goal complete via the free-text box instead.

    A cancelled goal (see cancel_goal()) is a no-op here too, same
    reasoning as apply_feedback() - never a save_plan() call that could
    silently revive it.
    """
    if latest.get("cancelled"):
        return latest

    steps = latest["plan"].get("steps")
    if not steps:
        # Nothing to advance - no step list on this goal at all (see
        # generate_plan(): only goals with a resolvable duration get one).
        return latest

    current = latest.get("current_step", 0)
    if current >= len(steps):
        # Already at "all steps done" - nothing left to confirm.
        return latest

    if done:
        next_index = current + 1
        if next_index >= len(steps):
            feedback_text = f"Completed step {current + 1} (the last one): {steps[current]}. All steps done."
        else:
            feedback_text = f"Completed step {current + 1}: {steps[current]}"
    else:
        next_index = current
        feedback_text = f"Not done yet: step {current + 1}: {steps[current]}"

    return save_plan(
        latest["goal"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=next_index,
        vision_id=latest.get("vision_id"),
    )


# ============================================================
# 8. Vision management
# ============================================================


def set_goal_vision(goal_id: int, vision_id: int | None) -> dict | None:
    """
    Add, move, or remove a goal's Vision link - the manual counterpart
    to `create_goal()`'s one-time choice, letting it be changed later
    (see docs/03-architecture.md § Vision). `vision_id=None` removes
    the goal from whichever Vision it currently has.

    Unlike advance_step()/apply_feedback() (which take an
    already-resolved `latest` record - the caller looks it up so a
    route-specific "stale tab" redirect can happen around the call),
    this resolves `goal_id` itself, since the route calling it has no
    other reason to look the record up first.

    Returns the newly saved record, or None if the change is
    rejected - never partially applied, and never raises for an
    ordinary bad input:
    - `goal_id` doesn't resolve to any goal.
    - `vision_id` is given but no such Vision exists (a stale/tampered
      value - the real UI always offers ids from `load_visions()`, so
      this is a defensive check, not the normal path).
    - the goal's latest record has an unanswered `clarification` -
      the next thing saved for this goal_id needs to be the answer to
      that question (see `apply_feedback()`'s clarification branch,
      which reads the newest `feedback` in this goal's history as
      exactly that answer). A Vision-change record saved in between
      would be misread as the answer instead, corrupting the next
      `generate_plan()` call's goal text - rejecting outright avoids
      that rather than trying to special-case it later.

    Requesting the Vision the goal is already linked to (or already
    has none, for `vision_id=None`) is a genuine no-op - returns
    `latest` unchanged rather than appending an identical record. A
    cancelled goal (see cancel_goal()) is also a no-op here, same
    reasoning as apply_feedback()/advance_step() - never a save_plan()
    call that could silently revive it.

    Preserves `plan`, `duration`, `frozen_duration`, `current_step`,
    and `completed` from the latest record exactly as they were -
    this changes which Vision the goal belongs to, nothing about the
    goal/plan itself, so nothing else about it should look any
    different than it did the moment before.
    """
    latest = get_latest_for_goal(goal_id)
    if latest is None:
        return None
    if latest["plan"].get("clarification"):
        return None
    if latest.get("cancelled"):
        return latest

    previous_vision_id = latest.get("vision_id")
    if vision_id == previous_vision_id:
        return latest

    if vision_id is None:
        feedback_text = "Removed from Vision"
    else:
        vision = get_vision(vision_id)
        if vision is None:
            return None
        verb = "Moved to" if previous_vision_id is not None else "Added to"
        feedback_text = f"{verb} Vision: {vision['text']}"

    return save_plan(
        latest["goal"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        completed=latest.get("completed", False), vision_id=vision_id,
    )


def archive_vision(vision_id: int) -> dict | None:
    """
    Archive a Vision (data_persistence.archive_vision()) and detach it
    from every currently-active Goal that references it - an archived
    Vision is no longer an active direction, so an active Goal
    shouldn't keep showing a current tie to it. Vision and Goal have
    independent lifecycles: this never changes a Goal's plan, duration,
    current_step, or completed/cancelled status - only which Vision (if
    any) it currently points to.

    Completed/cancelled Goals keep their vision_id unchanged - already
    a closed, historical record, not a claim that the Vision is still
    active, so there's nothing to detach.

    Detaching reuses set_goal_vision(goal_id, None) per Goal rather
    than writing a second way to change a Goal's Vision link, so it
    inherits that function's exact safety checks - in particular, a
    Goal with an unanswered `clarification` is left untouched (never
    revived or corrupted, see set_goal_vision()'s docstring) rather
    than forced; it simply keeps its stale vision_id until it's next
    touched. Like set_goal_vision(), this appends a new record per
    affected Goal (goal_id carried forward) - no existing record is
    ever mutated or removed.

    Returns the archived Vision record (or the already-archived one,
    unchanged, on a repeat call), or None if vision_id doesn't exist.
    """
    vision = archive_vision_record(vision_id)
    if vision is None:
        return None

    for latest in get_latest_for_all_goals():
        if (latest.get("vision_id") == vision_id
                and not latest.get("completed")
                and not latest.get("cancelled")):
            set_goal_vision(latest["goal_id"], None)

    return vision


# ============================================================
# 9. Cancellation
# ============================================================


def cancel_goal(goal_id: int) -> dict | None:
    """
    Mark a goal as cancelled (abandoned) - a distinct terminal status
    from `completed`, not a UI-level relabeling of it and not a third
    planning decision. Preserves `plan`, `duration`, `frozen_duration`,
    `current_step`, and `vision_id` from the latest record exactly as
    they were, so the goal's own data/history is never lost, only
    marked as no longer being pursued (still visible in full on
    /history, same as any other goal).

    Unlike set_goal_vision(), an unanswered `clarification` does NOT
    block this. set_goal_vision() refuses specifically because the
    NEXT record saved for this goal_id is expected to answer that
    clarification (see its docstring) - cancelling doesn't create that
    expectation, since nothing further will ever be asked about a
    cancelled goal. Abandoning a goal that never got past its first
    question is exactly the ordinary case for Cancel, not a hazard to
    guard against.

    Returns the newly saved record, or None if the change is
    rejected - never partially applied:
    - `goal_id` doesn't resolve to any goal.
    - the goal is already completed - a finished goal doesn't also
      become abandoned; one terminal status wins, and completion,
      already decided, isn't overwritten by a later Cancel click.

    Requesting cancellation on an already-cancelled goal is a genuine
    no-op - returns `latest` unchanged rather than appending an
    identical record (same idiom as set_goal_vision()).
    """
    latest = get_latest_for_goal(goal_id)
    if latest is None:
        return None
    if latest.get("completed"):
        return None
    if latest.get("cancelled"):
        return latest

    return save_plan(
        latest["goal"], latest["plan"], feedback="Cancelled",
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"), cancelled=True,
    )


# ============================================================
# 10. CLI entry point
# ============================================================

if __name__ == "__main__":
    my_goal = input("What do you want to achieve? ")
    print("\nThinking...\n")
    plan = generate_plan(my_goal)

    for horizon, text in plan.items():
        print(f"{horizon}: {text}")

    record = save_plan(my_goal, plan)
    print(f"\n[Saved as entry #{record['id']} in data/plans.json]")
