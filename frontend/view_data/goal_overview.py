"""
Goal Overview

View shaping for frontend's goal-overview pages (index.html,
completed_goal/_completed.html) - grouping and splitting the raw
history backend/goals/goal/resolver.py already resolves into the
specific shapes those two templates need. No Flask dependency.

Presentation-only, not a general Goal/Vision capability - deliberately
kept out of goal/resolver.py, which only resolves goal_id identity,
not presentation shape (see get_latest_for_all_goals()'s and
build_goal_overview()'s docstrings).
"""

from backend.goals.goal.resolver import created_at_key, get_latest_for_all_goals


def group_active_by_vision(active_records: list[dict], visions: list[dict]) -> list[tuple[dict | None, list[dict]]]:
    """
    Group active goal records by vision_id, for index.html - goals
    sharing a Vision render together under its heading; goals with no
    vision_id (the normal case) render in their own group, unheaded,
    last. Returns a list of (vision_record_or_None, [records]) pairs,
    vision groups oldest-vision-first, the no-vision group always last
    regardless of where it would otherwise fall.

    Presentation-only grouping for this one page, not a general Goal/
    Vision capability - deliberately kept here rather than added to
    goal/resolver.py (which only resolves goal_id identity, not
    presentation shape - see build_goal_overview() below - and is
    unchanged by Vision existing at all).
    """
    visions_by_id = {v["id"]: v for v in visions}
    groups: dict[int | None, list[dict]] = {}
    for record in active_records:
        groups.setdefault(record.get("vision_id"), []).append(record)

    with_vision = sorted(
        ((visions_by_id[vid], records) for vid, records in groups.items() if vid in visions_by_id),
        key=lambda pair: pair[0]["id"],
    )
    without_vision = groups.get(None, [])
    return with_vision + ([(None, without_vision)] if without_vision else [])


def build_goal_overview() -> dict:
    """
    Split every goal's latest record into "active" and "completed",
    for the goal overview views (index.html, completed_goal/_completed.html).
    Presentation-only shaping - see get_latest_for_all_goals()'s docstring
    for why this doesn't live in goal/resolver.py.

    Returns {"active": [...], "completed": [...]}. "active" is newest
    first; "completed" stays in the order it always has (oldest-first,
    by when each goal_id first appeared in history).
    """
    latest = get_latest_for_all_goals()
    # .get(), not [] - records saved before the "completed" field
    # existed don't have the key at all.
    active = [r for r in latest if not r.get("completed")]
    completed = [r for r in latest if r.get("completed")]
    active.sort(key=created_at_key, reverse=True)
    return {"active": active, "completed": completed}
