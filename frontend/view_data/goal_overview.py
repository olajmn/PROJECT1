"""
Goal Overview

View shaping for the goal-overview pages (index.html,
completed_goal/_completed.html) - grouping and splitting records that
goal/resolver.py already resolves. No Flask dependency; presentation
only, not Goal/Vision domain logic - resolver.py owns identity, this
module owns shape.
"""

from backend.goals.goal.resolver import created_at_key, get_latest_for_all_goals


def group_active_by_vision(active_records: list[dict], visions: list[dict]) -> list[tuple[dict | None, list[dict]]]:
    """
    Group active goals by Vision for index.html. Goals sharing a Vision
    render together under it; goals with none form an unheaded group,
    always last. Vision groups are ordered by Vision ID.
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
    Split the latest record for every goal into {"active": [...],
    "completed": [...]}. Active is newest-first; completed keeps its
    existing oldest-first order.
    """
    latest = get_latest_for_all_goals()
    # .get(), not [] - records saved before the "completed" field
    # existed don't have the key at all.
    active = [r for r in latest if not r.get("completed")]
    completed = [r for r in latest if r.get("completed")]
    active.sort(key=created_at_key, reverse=True)
    return {"active": active, "completed": completed}
