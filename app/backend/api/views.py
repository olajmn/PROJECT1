"""
JSON shapes the HTTP API returns to ui/ — manifestation + store reads,
not domain decisions.
"""

# Contents
#  1. Goal / history / chat-focus
#      - goal_view()
#      - active_goals() / completed_goals()
#      - HISTORY_PLAN_FIELDS / history_view()
#      - chat_focus_view()
#
#  2. Session log
#      - session_goal_event() / session_vision_event()
#      - session_log_view()
#
#  3. Vision / Steps tree
#      - vision_view()
#      - step_view() / tree_view()
#      - ancestor_labels()

from backend.agent.manifestation import surface_text, to_planning_node
from backend.store.data_persistence import load_history, load_visions, record_project_id
from backend.project.panes.chat.thread import thread_for
from backend.project.panes.create.resolver import created_at_key, get_latest_for_all_goals, get_latest_for_goal
from backend.project.panes.canvas.bead import Step
from backend.api import state


# ============================================================
# 1. View builders
# ============================================================


def goal_view(record: dict, reply: str | None = None) -> dict:
    """The one shape every /api/projects (and deprecated /api/goals)
    response uses for a single project — identity, display text,
    completion, plus manifestation. `project_id` is canonical;
    `goal_id` is a deprecated mirror for one release (Phase B).
    """
    pid = record_project_id(record)
    try:
        node = to_planning_node(record)
    except Exception as e:
        print(f"(debug: to_planning_node() failed for project {pid}: {e})")
        node = None
    return {
        "project_id": pid,
        "goal_id": pid,  # deprecated mirror — remove after alias period
        "goal": record["goal"],
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "vision_id": record.get("vision_id"),
        "surface": surface_text(record),
        "node": node,
        "thread": thread_for(pid, reply) if pid is not None else [],
        "reply": reply,
    }


def active_goals() -> list[dict]:
    """Every project that's neither completed nor cancelled, newest-first."""
    latest = get_latest_for_all_goals()
    active = [r for r in latest if not r.get("completed") and not r.get("cancelled")]
    active.sort(key=created_at_key, reverse=True)
    return active


def completed_goals() -> list[dict]:
    """Every project marked completed — cancelled are excluded.
    Oldest-first (unlike active_goals())."""
    latest = get_latest_for_all_goals()
    completed = [r for r in latest if r.get("completed")]
    completed.sort(key=created_at_key)
    return completed


# The plan fields worth showing in a history entry, in a fixed,
# readable order - not every key in the raw plan dict (e.g. `steps`
# renders as a count, not the full nested tree; History is a log to
# scan, not another place to render the live plan tree Active already
# shows).
HISTORY_PLAN_FIELDS = (
    "clarification", "suggested_action", "suggested_duration",
    "year", "month", "week", "today", "hour", "minute", "now",
)


def history_view(record: dict) -> dict:
    """One raw history entry as a plain key:value dump — closer to the
    unfiltered log than to goal_view()'s curated, UI-ready shape.
    History shows every record ever saved (not just the latest per
    project — see load_history()), so it shows what was actually saved,
    not a live status."""
    plan = record.get("plan") or {}
    steps = plan.get("steps")
    pid = record_project_id(record)
    return {
        "id": record["id"],
        "project_id": pid,
        "goal_id": pid,  # deprecated mirror
        "goal": record["goal"],
        "duration": record.get("duration"),
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "feedback": record.get("feedback"),
        "created_at": record["created_at"],
        "plan": {key: plan.get(key) for key in HISTORY_PLAN_FIELDS if plan.get(key)},
        "step_count": len(steps) if steps else 0,
    }


def chat_focus_view() -> dict:
    """{project_id, goal_id, goal} — which project, if any, free
    conversation is focused on. project_id is canonical; goal_id is a
    deprecated mirror. ChatFocus attribute name remains goal_id this
    round (Python symbol rename is a follow-up).
    """
    goal_id = state.session.chat_focus.goal_id
    if goal_id is None:
        return {"project_id": None, "goal_id": None, "goal": None}
    latest = get_latest_for_goal(goal_id)
    return {
        "project_id": goal_id,
        "goal_id": goal_id,
        "goal": latest["goal"] if latest else None,
    }


def session_goal_event(record: dict) -> dict:
    """One line in a Session's derived log for a project/plan record."""
    pid = record_project_id(record)
    return {
        "project_id": pid,
        "goal_id": pid,  # deprecated mirror
        "goal": record["goal"],
        "feedback": record.get("feedback"),
        "created_at": record["created_at"],
    }


def session_vision_event(vision: dict) -> dict:
    """One line in a Session's derived log for a Vision - only ever a
    creation event, since archiving isn't timestamped yet (see
    data_persistence.archive_vision()'s own docstring)."""
    return {
        "vision_id": vision["id"],
        "text": vision["text"],
        "created_at": vision["created_at"],
    }


def session_log_view(record: dict, window_end: str | None) -> dict:
    """A persisted Session record plus everything that happened during
    it - derived at read time, not logged by any mutating route: every
    load_history()/load_visions() entry whose `created_at` falls
    inside [started_at, window_end or now) belongs to this Session,
    because nothing else currently could have created it.

    `window_end` is NOT simply `record["ended_at"]` (always None today
    - see session.start_session()) - it's computed by the
    do_GET route below as the next Session's own `started_at`, since a
    later Session starting is the only signal available yet that an
    earlier one stopped being "the current one". Without this, every
    Session before the most recent would look open forever and match
    every event that happened after it, not just its own - reproduced
    and fixed within this same 2026-09-12 session. Reported back as
    this view's own `ended_at`: a best-available boundary, not
    necessarily a moment a real shutdown was ever observed. Only the
    single most recent Session (no successor) gets `window_end=None`,
    genuinely still open.

    Both event lists are sorted oldest-first, independent of
    load_history()'s own newest-first order, so the Session page reads
    as a timeline."""
    start = record["started_at"]
    end = window_end
    goal_events = sorted(
        (
            session_goal_event(r) for r in load_history()
            if start <= r["created_at"] and (end is None or r["created_at"] < end)
        ),
        key=lambda e: e["created_at"],
    )
    vision_events = sorted(
        (
            session_vision_event(v) for v in load_visions()
            if start <= v["created_at"] and (end is None or v["created_at"] < end)
        ),
        key=lambda e: e["created_at"],
    )
    return {
        "id": record["id"],
        "started_at": start,
        "ended_at": end,
        "goal_events": goal_events,
        "vision_events": vision_events,
    }


def vision_view(vision: dict) -> dict:
    """{id, text, archived, created_at} - load_visions()'s own record
    shape already has exactly these fields, `archived` just isn't
    guaranteed present (see data_persistence.archive_vision(), only
    ever set once true) - normalized to always-present here so the UI
    doesn't need to know that."""
    return {
        "id": vision["id"],
        "text": vision["text"],
        "archived": bool(vision.get("archived")),
        "created_at": vision["created_at"],
    }


def step_view(step: Step) -> dict:
    """A Step as the Steps page needs it: the PlanningNode fields the
    UI's tree renderer already understands, plus `zoomed` (see
    state.tree_zoomed) so a childless step can say whether it is unexplored
    or settled."""
    return {
        "id": step.id,
        "label": step.label,
        "status": "done" if step.resolved else "open",
        "zoomed": step.id in state.tree_zoomed,
        "children": [step_view(child) for child in step.children],
    }


def tree_view() -> dict:
    return {"duration": state.tree_duration, "root": step_view(state.tree) if state.tree else None}


def ancestor_labels(root: Step, step_id: str) -> list[str] | None:
    """The labels on the path from `root` down to (not including)
    `step_id`, outermost first - what zoom_into() wants as context.
    None if `step_id` isn't in this tree. Recomputed by walking rather
    than stored as parent links on Step, which would make the tree
    cyclic and so unserializable (see step.py's own docstring)."""
    if root.id == step_id:
        return []
    for child in root.children:
        below = ancestor_labels(child, step_id)
        if below is not None:
            return [root.label, *below]
    return None


