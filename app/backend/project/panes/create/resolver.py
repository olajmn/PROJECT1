"""
Read and interpret project history.

This module does not store anything - it reads via project_persistence
and answers, by project_id:

- What is the full event tape for this project?
- What is the current SoT record for this project?
- What is the current record for every project that exists?

Whether a project counts as "active" or "completed", and how projects
get grouped or sorted for display, is board-building logic, not project
identity.

project_id itself is minted in project_persistence.py (_next_goal_id()),
not here - moving it here would create a circular import between the two
modules. See docs/05-decisions.md for why identity is a minted id, not
the project's display name.
"""

from datetime import datetime

from backend.store.project_persistence import (
    load_all_currents,
    load_current,
    load_project_history,
)


# Timestamp handling


def created_at_key(record: dict) -> datetime:
    """
    Make created_at values comparable across old and new formats.

    Records saved before 2026-08-21 stored timezone-aware UTC
    timestamps (e.g. "...+00:00"); newer records store naive local
    time. Comparing an aware and a naive datetime raises TypeError, so
    aware timestamps are converted to local time and stripped of
    tzinfo here.

    Public (not `_`-prefixed) because frontend/view_data/goal_overview.py
    needs it too, to sort the board it builds from get_latest_for_all_projects().
    """
    parsed = datetime.fromisoformat(record["created_at"])
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


# Read one goal


def get_history_for_project(project_id: int) -> list[dict]:
    """
    Return every record for one project_id, oldest first - the full
    back-and-forth of feedback and replanning for this project.

    Parameter name project_id kept this round; matches project_id on disk.
    Reads that project's events tape (data/projects/{id}/events.jsonl).
    """
    return load_project_history(project_id)


def get_latest_for_project(project_id: int) -> dict | None:
    """
    Return the current SoT record for one project_id, or None.

    Distinct from project_persistence.get_latest_plan(), which answers
    "what was touched most recently across every project" - not safe once
    two projects can be active side by side (see docs/06-development.md).
    """
    return load_current(project_id)


def get_latest_for_all_projects() -> list[dict]:
    """
    Return the current SoT record for every project_id - one
    project, one record.
    """
    return load_all_currents()
