"""
Goal Overview

View shaping for the goal-overview pages (index.html,
completed_goal/_completed.html) - grouping and splitting records that
goal/resolver.py already resolves. No Flask dependency; presentation
only, not Goal/Vision domain logic - resolver.py owns identity, this
module owns shape.
"""

from backend.goals.goal.resolver import created_at_key, get_latest_for_all_goals


def group_goals_by_vision_id(active_records: list[dict]) -> dict[int, list[dict]]:
    """
    Active goals keyed by vision_id, dropping the ones with none - the
    Vision page's per-Vision lookup (`goals_by_vision.get(v.id, [])`
    for whichever Vision is currently being rendered).
    """
    result: dict[int, list[dict]] = {}
    for record in active_records:
        vision_id = record.get("vision_id")
        if vision_id is not None:
            result.setdefault(vision_id, []).append(record)
    return result


def build_goal_overview() -> dict:
    """
    Split the latest record for every goal into {"active": [...],
    "completed": [...]}. Active is newest-first; completed keeps its
    existing oldest-first order.

    A cancelled goal (see planner.cancel_goal()) is excluded from both
    - cancelled is its own status, not a kind of completed, so it
    doesn't belong in the Completed list. It isn't dropped from
    history: /history reads every record directly via
    data_persistence.load_history(), independent of this split, so a
    cancelled goal stays fully visible there.
    """
    latest = get_latest_for_all_goals()
    # .get(), not [] - records saved before the "completed"/"cancelled"
    # fields existed don't have the keys at all.
    active = [r for r in latest if not r.get("completed") and not r.get("cancelled")]
    completed = [r for r in latest if r.get("completed")]
    active.sort(key=created_at_key, reverse=True)
    return {"active": active, "completed": completed}
