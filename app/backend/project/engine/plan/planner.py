"""
Planner
=======

Goal -> structured Plan, via a local LLM (Ollama). Produces a plan
across seven time horizons and revises it (replan()). Minting or
abandoning a Goal is create/lifecycle.py, which calls generate_plan()
(Stage 3 - see generate_plan.py) on create. Acting on a free-text note
against an existing goal is feedback/route_note.py, which calls back
into generate_plan()/replan() here. Never talks to the model directly
(see json_request.py/plan_structure.py).

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull qwen3.5:9b) - see
backend/llm_client.py for the one place the concrete model is
actually named.

PLAN_KEYS and prompt-grounding helpers live in plan_schema.py;
Stage 3 Decide lives in decide.py, orchestrated by generate_plan.py
(Fill + steps when planable). Re-exported here so existing
`planner.generate_plan` / `planner.PLAN_KEYS` callers keep working.
See docs/06-development.md for this file's naming/reorganization
history.

Run from the PROJECT ROOT: .venv/bin/python -m backend.goals.plan.planner
"""

# Contents
#  1. Re-exports (schema + Stage 3 orchestration)
#      - PLAN_KEYS, generate_plan, _planability, …
#
#  2. Frozen duration for save
#      - frozen_duration_for()
#
#  3. Replanning
#      - replan()
#      - apply_new_duration()
#
#  4. Step handling
#      - advance_step()
#
#  5. Vision management
#      - set_goal_vision()
#      - archive_vision()
#
#  6. CLI entry point
#      (module execution block; no named function)

from backend.foundation.time import freeze_duration, resolve_duration
from backend.project.panes.create.resolver import get_latest_for_all_goals, get_latest_for_goal
from backend.store.data_persistence import archive_vision as archive_vision_record, get_vision, save_plan
from backend.project.engine.plan import generate_plan as generate_plan_mod
from backend.project.engine.plan.json_request import ask_model
from backend.project.engine.plan.plan_prompts import REPLAN_SYSTEM_PROMPT
from backend.project.engine.plan.plan_schema import (
    PLAN_KEYS,
    _horizon_scope_instruction,
    _now_str,
)

# ============================================================
# 1. Re-exports (schema + Stage 3)
# ============================================================

# Callers that use `planner.*` (lifecycle, route_note, tests).
generate_plan = generate_plan_mod.generate_plan
OPENING_CLARIFICATION = generate_plan_mod.OPENING_CLARIFICATION
_planability = generate_plan_mod._planability
_reject_opening_action = generate_plan_mod._reject_opening_action


# ============================================================
# 2. Frozen duration for save
# ============================================================


def frozen_duration_for(plan: dict, duration: str | None) -> dict | None:
    """
    The frozen_duration to save alongside `plan` - None while `plan` is
    a clarification or a proposed-but-unconfirmed suggested_duration
    (nothing has actually started yet, so there's no honest countdown
    to freeze), otherwise freeze_duration(duration). Shared by
    generate_plan()'s and replan()'s callers (frontend/app.py) so this
    rule is expressed once instead of repeated at every call site that
    saves a plan.
    """
    if plan.get("clarification") or plan.get("suggested_duration") or plan.get("suggested_action"):
        return None
    return freeze_duration(duration)


# ============================================================
# 3. Replanning
# ============================================================


def replan(goal: str, history: list[dict], feedback: str, duration: str | None = None, vision_id: int | None = None) -> dict:
    """
    Takes the goal, its full history (oldest first), and feedback on
    the most recent "now" action, and asks the model for an
    updated plan. Returns the same shape as generate_plan().

    Passing the *whole* history, not just the previous plan, is what
    lets REPLAN_SYSTEM_PROMPT's "don't shrink 'now' more than once"
    rule work - a model shown only the last step can't notice it has
    already made the same task smaller several times in a row (see
    docs/06-development.md, 2026-08-20, for the drift this fixed).

    `vision_id` - same optional, separately-sectioned background
    context as generate_plan()'s (added 2026-09-06): a Goal's linked
    Vision is meant to follow it for the goal's whole lifetime, not
    just its first plan, so every replan gets the same context the
    initial plan did (see docs/planning-model.md, the authority on
    Vision).
    """
    # Named history_lines, not "steps" - unrelated to this file's
    # `steps` plan field/plan_structure.generate_structure() (added
    # later the same day); this is prose lines for the replan prompt,
    # not the step list.
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
    if vision_id is not None:
        vision = get_vision(vision_id)
        if vision is not None:
            user_content += f"\n\nThis goal is part of a broader direction: {vision['text']}"
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
    plan = generate_plan(existing["goal"], duration, vision_id=existing.get("vision_id"))
    return save_plan(
        existing["goal"], plan, feedback=feedback, duration=duration, goal_id=existing["goal_id"],
        frozen_duration=frozen_duration_for(plan, duration),
        vision_id=existing.get("vision_id"),
    )


# ============================================================
# 4. Step handling
# ============================================================


def advance_step(latest: dict, done: bool, resolved: bool = False) -> dict:
    """
    Records the outcome of the current step's Action, and moves
    `current_step` only when the Step it was attempted for is actually
    resolved - not merely because an Action was reported done. See
    docs/planning-model.md: an Action being completed never, by
    itself, means its Step is realized.

    `done`/`resolved` come from active_goal/_task.html's three-way
    Done? control (never inferred from free text - see
    docs/05-decisions.md):
    - done=False: the Action wasn't done. Same safe, no-replan
      treatment as route_note()'s "in_progress"; the pointer and
      the step's status both stay exactly as they were.
    - done=True, resolved=False: the Action was done, but the user says
      the Step itself isn't resolved yet (e.g. searched for a gym, but
      hasn't found/picked one) - logged, but `current_step` still
      doesn't move, since there's nothing left to advance PAST yet.
    - done=True, resolved=True: the Step is now resolved - only this
      case advances `current_step`, exactly once.

    `step_status` is a per-step "open"/"resolved" list, parallel-
    indexed to `steps`, carried on the record next to `current_step`
    (see data_persistence.save_plan()) - defaults to every step "open"
    when missing or the wrong length (no step_status yet on this
    record, or a goal saved before this field existed), the same safe-
    fallback idiom as `current_step`'s own `.get(..., 0)` default. Only
    the step actually being resolved is ever written to "resolved" -
    this function never marks any other index, past or future.

    `current_step` can still reach `len(steps)` (one past the last
    valid index) to mean "every step is resolved" - unchanged from
    before, still what active_goal/_task.html uses to prompt marking
    the whole goal complete via the free-text box instead.

    A cancelled goal (see cancel_goal()) is a no-op here too, same
    reasoning as route_note() - never a save_plan() call that could
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

    existing_status = latest.get("step_status")
    if not existing_status or len(existing_status) != len(steps):
        existing_status = ["open"] * len(steps)
    status = list(existing_status)

    if not done:
        next_index = current
        feedback_text = f"Not done yet: step {current + 1}: {steps[current]}"
    elif resolved:
        status[current] = "resolved"
        next_index = current + 1
        if next_index >= len(steps):
            feedback_text = f"Completed step {current + 1} (the last one): {steps[current]}. All steps done."
        else:
            feedback_text = f"Completed step {current + 1}: {steps[current]}"
    else:
        next_index = current
        feedback_text = f"Worked on step {current + 1} (not yet resolved): {steps[current]}"

    return save_plan(
        latest["goal"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=next_index,
        vision_id=latest.get("vision_id"), step_status=status,
    )


# ============================================================
# 5. Vision management
# ============================================================


def set_goal_vision(goal_id: int, vision_id: int | None) -> dict | None:
    """
    Add, move, or remove a goal's Vision link - the manual counterpart
    to `create_goal()`'s one-time choice, letting it be changed later
    (see docs/planning-model.md, the authority on Vision).
    `vision_id=None` removes
    the goal from whichever Vision it currently has.

    Unlike advance_step()/route_note() (which take an
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
      that question (see `route_note()`'s clarification branch,
      which reads the newest `feedback` in this goal's history as
      exactly that answer). A Vision-change record saved in between
      would be misread as the answer instead, corrupting the next
      `generate_plan()` call's goal text - rejecting outright avoids
      that rather than trying to special-case it later.

    Requesting the Vision the goal is already linked to (or already
    has none, for `vision_id=None`) is a genuine no-op - returns
    `latest` unchanged rather than appending an identical record. A
    cancelled goal (see cancel_goal()) is also a no-op here, same
    reasoning as route_note()/advance_step() - never a save_plan()
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
        step_status=latest.get("step_status"),
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
# 7. CLI entry point
# ============================================================

if __name__ == "__main__":
    my_goal = input("What do you want to achieve? ")
    print("\nThinking...\n")
    plan = generate_plan(my_goal)

    for horizon, text in plan.items():
        print(f"{horizon}: {text}")

    record = save_plan(my_goal, plan)
    print(f"\n[Saved as entry #{record['id']} in data/plans.jsonl]")
