"""
Read and interpret goal history.

This module does not store anything - it reads history via
data_persistence and answers, by project_id:

- What is the full history of this goal?
- What is the latest record for this goal?
- What is the latest record for every goal that exists?

Whether a goal counts as "active" or "completed", and how goals get
grouped or sorted for display, is board-building logic, not goal
identity - see frontend/view_data/goal_overview.py, where the board is
actually built.

project_id itself is minted in data_persistence.py (_next_project_id()), not
here - moving it here would create a circular import between the two
modules. See docs/05-decisions.md for why identity is a minted id, not
the goal's text.
"""

from datetime import datetime

from backend.store.data_persistence import (
    load_history,
    load_project_history,
    record_project_id,
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
    Reads that project's file only (data/projects/{id}.jsonl).
    """
    return load_project_history(project_id)


def get_latest_for_project(project_id: int) -> dict | None:
    """
    Return the most recent record for one project_id, or None.

    Distinct from data_persistence.get_latest_plan(), which answers
    "what was touched most recently across every project" - not safe once
    two projects can be active side by side (see docs/06-development.md).
    """
    history = load_project_history(project_id)
    return history[-1] if history else None


# Read all goals


def get_latest_for_all_projects() -> list[dict]:
    """
    Return the latest record for every project_id in history - one
    project, one record.

    Order is just whatever falls out of scanning history oldest-first
    and keeping the last record seen per project_id - not meaningful on
    its own.
    """
    latest_by_goal: dict[int, dict] = {}
    for record in load_history():
        pid = record_project_id(record)
        if pid is not None:
            latest_by_goal[pid] = record
    return list(latest_by_goal.values())
