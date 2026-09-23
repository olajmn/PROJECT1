"""
Replace a project's display name. Identity stays project_id.

The typed label is arbitrary — this module only writes it. Resolver
still groups records; the map only paints the result.
"""

from backend.store.data_persistence import set_project_name
from backend.project.panes.create.resolver import get_latest_for_goal


def rename_project(goal_id: int, name: str) -> dict | None:
    """
    Replace the project's display name. Identity stays `project_id`.

    Empty text is refused. The same name is a no-op (returns latest
    unchanged). The write is set_project_name() — latest record only,
    not a new history line — so chat does not gain a rename turn.
    """
    label = name.strip()
    if not label:
        return None
    latest = get_latest_for_goal(goal_id)
    if latest is None:
        return None
    if latest.get("goal") == label:
        return latest
    return set_project_name(goal_id, label)
