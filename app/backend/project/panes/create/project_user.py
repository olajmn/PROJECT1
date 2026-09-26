"""
Link a project to an id#N, or archive an id and detach its projects.

Identity writes, not reasoning. Judgment does not own this.
"""

from backend.project.panes.create.resolver import (
    get_latest_for_all_projects,
    get_latest_for_project,
)
from backend.store.users_persistence import (
    archive_user as archive_user_record,
    get_user,
)
from backend.store.project_persistence import save_plan


def set_project_user(project_id: int, sim_user_id: int | None) -> dict | None:
    """
    Add, move, or remove a project's id link after mint (see
    docs/planning-model.md, the authority on Vision).
    `sim_user_id=None` removes the project from whichever id it
    currently has.

    Unlike chat's talk() (which takes an already-resolved `latest`
    record), this resolves `project_id` itself, since the route calling
    it has no other reason to look the record up first.

    Returns the newly saved record, or None if the change is
    rejected - never partially applied, and never raises for an
    ordinary bad input:
    - `project_id` doesn't resolve to any goal.
    - `sim_user_id` is given but no such Vision exists (a stale/tampered
      value - the real UI always offers ids from `load_users()`, so
      this is a defensive check, not the normal path).

    Requesting the Vision the goal is already linked to (or already
    has none, for `sim_user_id=None`) is a genuine no-op - returns
    `latest` unchanged rather than appending an identical record. A
    cancelled goal (see cancel_project()) is also a no-op here — never
    a save_plan() call that could silently revive it.

    Preserves `plan`, `duration`, `frozen_duration`, `current_step`,
    and `completed` from the latest record exactly as they were -
    this changes which Vision the goal belongs to, nothing about the
    goal/plan itself, so nothing else about it should look any
    different than it did the moment before.
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("cancelled"):
        return latest

    previous_sim_user_id = latest.get("sim_user_id")
    if sim_user_id == previous_sim_user_id:
        return latest

    if sim_user_id is None:
        feedback_text = "Removed from Vision"
    else:
        vision = get_user(sim_user_id)
        if vision is None:
            return None
        verb = "Moved to" if previous_sim_user_id is not None else "Added to"
        feedback_text = f"{verb} Vision: {vision['text']}"

    return save_plan(
        latest["name"], latest["plan"], feedback=feedback_text,
        duration=latest.get("duration"), project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"), current_step=latest.get("current_step", 0),
        completed=latest.get("completed", False), sim_user_id=sim_user_id,
        step_status=latest.get("step_status"), event="owner_changed",
    )


def archive_user(sim_user_id: int) -> dict | None:
    """
    Archive a simulated user (users_persistence.archive_user()) and detach it
    from every currently-active Goal that references it - an archived
    Vision is no longer an active direction, so an active Goal
    shouldn't keep showing a current tie to it. Vision and Goal have
    independent lifecycles: this never changes a Goal's plan, duration,
    current_step, or completed/cancelled status - only which Vision (if
    any) it currently points to.

    Completed/cancelled Goals keep their sim_user_id unchanged - already
    a closed, historical record, not a claim that the Vision is still
    active, so there's nothing to detach.

    Detaching reuses set_project_user(project_id, None) per Goal rather
    than writing a second way to change a Goal's Vision link, so it
    inherits that function's safety checks. Like set_project_user(),
    this appends a new record per affected Goal (project_id carried
    forward) - no existing record is ever mutated or removed.

    Returns the archived Vision record (or the already-archived one,
    unchanged, on a repeat call), or None if sim_user_id doesn't exist.
    """
    vision = archive_user_record(sim_user_id)
    if vision is None:
        return None

    for latest in get_latest_for_all_projects():
        if (latest.get("sim_user_id") == sim_user_id
                and not latest.get("completed")
                and not latest.get("cancelled")):
            set_project_user(latest["project_id"], None)

    return vision
