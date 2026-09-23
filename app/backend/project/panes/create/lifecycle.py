"""
A project's lifecycle: mint one, abandon one.

Identity and current state stay in resolver.py - this module only
writes. The ordinary mint is create_project() — a name and an empty
canvas, no engine. create_project_via_engine() is the leftover
opening door into run_stage3(); Create does not call it.
Renaming the label is rename.py. Cancelling never does. Vision is
accepted here as an optional link at birth, but linking/unlinking
later stays on project_user.set_project_user() until Vision's own
shape is decided.
"""

# Contents
#  1. Creation
#      - create_project()
#      - create_project_via_engine()
#
#  2. Cancellation
#      - cancel_goal()

from backend.foundation.time import extract_duration_phrase
from backend.store.data_persistence import save_plan, save_user
from backend.project.panes.create.resolver import get_latest_for_goal
from backend.project.engine.judgment.run_stage3 import run_stage3, _planability
from backend.project.engine.reason import frozen_duration_for


# ============================================================
# 1. Creation
# ============================================================


def create_project(typed_text: str, sim_user_id_value: str) -> dict:
    """
    Mint a project: a name and an empty canvas. No engine.

    The typed text is only a label. The tree arrives afterwards —
    built by hand, pasted, or walked in from a folder.
    """
    sim_user_id = int(sim_user_id_value) if sim_user_id_value else None
    return save_plan(
        typed_text,
        {"progression": {"steps": []}},
        sim_user_id=sim_user_id,
    )


def create_project_via_engine(
    typed_text: str, new_vision_text: str, sim_user_id_value: str,
) -> dict:
    """
    Mint by running reasoning on a sentence (`run_stage3`,
    opening=True). Not the Create pane — that uses create_project().

    One text field, not a separate goal/duration pair -
    `extract_duration_phrase()` searches the whole typed text for a
    recognized time phrase (e.g. "clean the apartment this weekend").
    If nothing recognized turns up, that's treated as "no timeframe
    given" DETERMINISTICALLY, before calling the model - same
    "code decides, model is just told" reasoning as
    judgment/shape._horizon_scope_instruction() (see docs/05-decisions.md, 2026-08-23).
    A missing timeframe no longer means "always ask" by itself, though:
    run_stage3()'s own model call also decides whether a default can
    be proposed instead (`suggested_duration`), or, for a goal that's
    already complete without a broader duration, simply returns a plan
    scoped to `now` alone. opening=True so that first mint cannot land
    on a suggested_action - opening is not "do this now". Missing
    duration no longer blocks a planable mint; Decide asks for a
    checkable End when the aim is vague. Time stays optional for
    co-building the WHAT line. `_planability()` reads that one
    response and gives the result an explicit, inspectable name
    ("ask"/"suggest"/"planable") - the reasoning step between a
    sentence and treating the engine result as real, not a second
    model call (see docs/planning-model.md § Minimum planability).

    Only ever starts a NEW project (mints its own project_id via
    save_plan()); extending an existing timeframe goes through
    route_note()'s requests_duration_change() branch instead.

    `frozen_duration` is left None when the plan comes back with
    `clarification` or `suggested_duration` set (nothing has actually
    started yet) - there's no honest countdown to draw until
    route_note() resolves either into a real plan. Frozen for real
    only once that happens.

    `new_vision_text` is checked before `sim_user_id_value` - typing a
    new Vision always wins over whatever the select had chosen.
    Neither is required; carried forward unchanged on every later
    replan for this project (a project's vision doesn't change just
    because the engine ran again).
    """
    if new_vision_text:
        sim_user_id = save_user(new_vision_text)["id"]
    elif sim_user_id_value:
        sim_user_id = int(sim_user_id_value)
    else:
        sim_user_id = None

    duration = extract_duration_phrase(typed_text)
    plan = run_stage3(typed_text, duration, sim_user_id=sim_user_id, opening=True)
    if _planability(plan) != "planable":
        # ask or suggest - nothing else in `plan` is real yet; duration
        # stays unrecorded until the next round resolves it (see
        # route_note()'s clarification/suggested_duration branches).
        return save_plan(typed_text, plan, duration=None, frozen_duration=None, sim_user_id=sim_user_id)
    return save_plan(
        typed_text, plan, duration=duration,
        frozen_duration=frozen_duration_for(plan, duration),
        sim_user_id=sim_user_id,
    )


# ============================================================
# 2. Cancellation
# ============================================================


def cancel_goal(goal_id: int) -> dict | None:
    """
    Mark a goal as cancelled (abandoned) - a distinct terminal status
    from `completed`, not a UI-level relabeling of it and not a third
    planning decision. Preserves `plan`, `duration`, `frozen_duration`,
    `current_step`, and `sim_user_id` from the latest record exactly as
    they were, so the goal's own data/history is never lost, only
    marked as no longer being pursued (still visible in full on
    /history, same as any other goal).

    Unlike set_project_user(), an unanswered `clarification` does NOT
    block this. set_project_user() refuses specifically because the
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
    identical record (same idiom as set_project_user()).
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
        sim_user_id=latest.get("sim_user_id"), cancelled=True,
        step_status=latest.get("step_status"),
    )
