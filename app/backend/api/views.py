"""
JSON shapes the HTTP API returns to ui/ — translate_nodes + store reads,
not domain decisions.
"""

# Contents
#  1. Goal / project
#      - goal_view()
#      - active_goals()
#
#  2. Simulated user
#      - user_view()

from backend.agent.translate_nodes import surface_text, to_planning_node
from backend.store.data_persistence import record_project_id
from backend.project.panes.chat.chart import talk_tree
from backend.project.panes.chat.thread import thread_for
from backend.project.panes.create.resolver import created_at_key, get_latest_for_all_goals


# ============================================================
# 1. View builders
# ============================================================


def goal_view(record: dict, reply: str | None = None) -> dict:
    """The one shape every /api/projects response uses for a single
    project — identity, display text, completion, plus translate_nodes.
    `project_id` is canonical.
    """
    pid = record_project_id(record)
    try:
        node = to_planning_node(record)
    except Exception as e:
        print(f"(debug: to_planning_node() failed for project {pid}: {e})")
        node = None
    thread = thread_for(pid, reply) if pid is not None else []
    return {
        "project_id": pid,
        "goal": record["goal"],
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "sim_user_id": record.get("sim_user_id"),
        "created_at": record.get("created_at"),
        "surface": surface_text(record),
        "node": node,
        "thread": thread,
        "talk": talk_tree(thread),
        "reply": reply,
    }


def active_goals() -> list[dict]:
    """Every project that's neither completed nor cancelled, newest-first."""
    latest = get_latest_for_all_goals()
    active = [r for r in latest if not r.get("completed") and not r.get("cancelled")]
    active.sort(key=created_at_key, reverse=True)
    return active


def user_view(user: dict) -> dict:
    """{id, text, archived, created_at} - load_users()'s own record
    shape already has exactly these fields; `archived` just isn't
    guaranteed present (only set once true) - normalized here so the
    UI doesn't need to know that."""
    return {
        "id": user["id"],
        "text": user["text"],
        "archived": bool(user.get("archived")),
        "created_at": user["created_at"],
    }
