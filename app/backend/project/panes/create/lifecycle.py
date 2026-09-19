"""
A Goal's lifecycle: mint one, abandon one.

Identity and current state stay in resolver.py - this module only
writes. Creating a goal still asks plan/planner.py to produce the
first plan (generate_plan); cancelling never does. Vision is accepted
here as an optional link at birth, but linking/unlinking later stays
on planner.set_goal_vision() until Vision's own shape is decided.
"""

# Contents
#  1. Creation
#      - create_goal()
#
#  2. Cancellation
#      - cancel_goal()

from backend.foundation.time import extract_duration_phrase
from backend.store.data_persistence import save_plan, save_vision
from backend.project.panes.create.resolver import get_latest_for_goal
from backend.project.engine.plan import planner


# ============================================================
# 1. Creation
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
    planner._horizon_scope_instruction() (see docs/05-decisions.md, 2026-08-23).
    A missing timeframe no longer means "always ask" by itself, though:
    generate_plan()'s own model call also decides whether a default can
    be proposed instead (`suggested_duration`), or, for a goal that's
    already complete without a broader duration, simply returns a plan
    scoped to `now` alone. create_goal() passes opening=True so that
    first mint cannot land on a suggested_action - opening is not
    "do this now". Missing duration no longer blocks a planable mint;
    Decide asks for a checkable End when the goal is vague. Time stays
    optional for co-building the WHAT line. `_planability()` reads that
    one response and gives the result an explicit, inspectable name
    ("ask"/"suggest"/"planable") - the reasoning step between a Goal
    and treating its plan as real, not a second model call (see
    docs/planning-model.md § Minimum planability).

    Only ever starts a NEW goal (mints its own goal_id via save_plan());
    extending an EXISTING goal's timeframe goes through
    route_note()'s requests_duration_change() branch instead.

    `frozen_duration` is left None when the plan comes back with
    `clarification` or `suggested_duration` set (nothing has actually
    started yet) - there's no honest countdown to draw until
    route_note() resolves either into a real plan. Frozen for real
    only once that happens.

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
    plan = planner.generate_plan(typed_text, duration, vision_id=vision_id, opening=True)
    if planner._planability(plan) != "planable":
        # ask or suggest - nothing else in `plan` is real yet; duration
        # stays unrecorded until the next round resolves it (see
        # route_note()'s clarification/suggested_duration branches).
        return save_plan(typed_text, plan, duration=None, frozen_duration=None, vision_id=vision_id)
    return save_plan(
        typed_text, plan, duration=duration,
        frozen_duration=planner.frozen_duration_for(plan, duration),
        vision_id=vision_id,
    )


# ============================================================
# 2. Cancellation
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
        duration=latest.get("duration"), goal_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"), cancelled=True,
        step_status=latest.get("step_status"),
    )
