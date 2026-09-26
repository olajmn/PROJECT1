"""
Rename a project. Identity stays project_id; only the display name changes.

A rename is saved as its own line (event "renamed"), so the project's
timeline keeps every name it has had. The chat does not show it.
"""

from backend.store.project_persistence import save_plan
from backend.project.panes.create.resolver import get_latest_for_project


def rename_project(project_id: int, name: str) -> dict | None:
    """The saved rename line, the unchanged latest line when the name is
    the same, or None for empty text or an unknown project."""
    label = name.strip()
    if not label:
        return None
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    old = latest.get("name") or ""
    if old == label:
        return latest
    return save_plan(
        label,
        latest.get("plan") or {},
        feedback=f"Renamed: {old} → {label}",
        duration=latest.get("duration"),
        completed=latest.get("completed", False),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="renamed",
    )
