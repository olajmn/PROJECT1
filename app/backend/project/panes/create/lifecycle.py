"""
A project's lifecycle: mint one, abandon one.

Identity and current state stay in resolver.py - this module only
writes. Mint is create_project() — a name and an empty canvas, no
engine. Renaming the label is rename.py. Cancelling never does.
Vision is accepted here as an optional link at birth, but
linking/unlinking later stays on project_user.set_project_user()
until Vision's own shape is decided.
"""

# Contents
#  1. Creation
#      - create_project()
#
#  2. Cancellation
#      - cancel_project()

from backend.store.data_persistence import save_plan
from backend.project.panes.create.resolver import get_latest_for_project


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
        event="created",
    )


# ============================================================
# 2. Cancellation
# ============================================================


def cancel_project(project_id: int) -> dict | None:
    """
    Mark a goal as cancelled (abandoned) - a distinct terminal status
    from `completed`, not a UI-level relabeling of it and not a third
    planning decision. Preserves `plan`, `duration`, `frozen_duration`,
    `current_step`, and `sim_user_id` from the latest record exactly as
    they were, so the goal's own data/history is never lost, only
    marked as no longer being pursued (still visible in full on
    /history, same as any other goal).

    Returns the newly saved record, or None if the change is
    rejected - never partially applied:
    - `project_id` doesn't resolve to any goal.
    - the goal is already completed - a finished goal doesn't also
      become abandoned; one terminal status wins, and completion,
      already decided, isn't overwritten by a later Cancel click.

    Requesting cancellation on an already-cancelled goal is a genuine
    no-op - returns `latest` unchanged rather than appending an
    identical record (same idiom as set_project_user()).
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("completed"):
        return None
    if latest.get("cancelled"):
        return latest

    return save_plan(
        latest["name"], latest["plan"], feedback="Cancelled",
        duration=latest.get("duration"), project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"), cancelled=True,
        step_status=latest.get("step_status"), event="archived",
    )
