"""
Shapes the data sent back to the browser: a project with its map tree
and chat, the project list, a simulated user. Only reads and reshapes;
no product rules.
"""

# Contents
#  1. Project, project list, account
#      - project_view()
#      - active_projects() / archived_projects()
#      - account_view()
#      - saved_tree_view()
#
#  2. Map tree
#      - map_tree()

from backend.storage.project_persistence import record_project_id
from backend.project.node import steps_of
from backend.project.status.build_status import build_status
from backend.project.panes.chat.screen.chat_thread import thread_for
from backend.project.panes.create.resolver import (
    created_at_key,
    get_history_for_project,
    get_latest_for_all_projects,
)


# ============================================================
# 1. Project, project list, user
# ============================================================


def project_view(
    record: dict,
    reply: str | None = None,
    select: dict | None = None,
    toggle_map_ids: bool = False,
) -> dict:
    """One project as the browser gets it after any project action:
    name, state, map tree, chat, and status (the panel above the chat).

    `reply` (a chat reply just made) is placed as the last message in
    `thread`, not sent as its own field. `select` (optional
    `{id, label}` from `/select`) tells the UI to focus that node.
    `toggle_map_ids` (from `/id` with no node selected) tells the UI to
    switch the map between ids and labels.
    """
    pid = record_project_id(record)
    try:
        node = map_tree(record)
    except Exception as e:
        # A broken tree must not hide the rest of the project.
        print(f"(debug: map_tree() failed for project {pid}: {e})")
        node = None
    history = get_history_for_project(pid) if pid is not None else []
    thread = thread_for(pid, reply, history) if pid is not None else []
    view = {
        "project_id": pid,
        "name": record["name"],
        "completed": bool(record.get("completed")),
        "cancelled": bool(record.get("cancelled")),
        "sim_user_id": record.get("sim_user_id"),
        "account_n": record.get("account_n"),
        "created_at": record.get("created_at"),
        "node": node,
        "thread": thread,
        "status": build_status(history, current=record),
    }
    if select and select.get("id") and select.get("label"):
        view["select"] = {
            "id": str(select["id"]),
            "label": str(select["label"]),
        }
    if toggle_map_ids:
        view["toggle_map_ids"] = True
    return view


def active_projects() -> list[dict]:
    """Every project that's neither completed nor cancelled, newest first."""
    latest = get_latest_for_all_projects()
    active = [r for r in latest if not r.get("completed") and not r.get("cancelled")]
    active.sort(key=created_at_key, reverse=True)
    return active


def archived_projects() -> list[dict]:
    """Cancelled or completed projects, newest first (Settings → Archive)."""
    latest = get_latest_for_all_projects()
    closed = [r for r in latest if r.get("completed") or r.get("cancelled")]
    closed.sort(key=created_at_key, reverse=True)
    return closed


def account_view(account: dict) -> dict:
    """{id, text, archived, created_at, archived_at?}. `archived` is only
    stored once true, so it is filled in here."""
    view = {
        "id": account["id"],
        "text": account["text"],
        "archived": bool(account.get("archived")),
        "created_at": account["created_at"],
    }
    if account.get("archived_at"):
        view["archived_at"] = account["archived_at"]
    return view


def saved_tree_view(saved: dict) -> dict:
    """{id, name, saved_at, node_count} — what the picker lists; the
    structure itself stays on the server until it is inserted."""
    def count(node: dict) -> int:
        return 1 + sum(count(c) for c in node.get("children") or [])

    return {
        "id": saved["id"],
        "name": saved["name"],
        "saved_at": saved["saved_at"],
        "node_count": count(saved.get("tree") or {}),
    }



# ============================================================
# 2. Map tree
# ============================================================


def map_tree(record: dict) -> dict | None:
    """The map as the browser draws it: {id, label, status, children},
    with the project as the root. None when the map is empty."""
    steps = steps_of(record)
    pid = record["project_id"]
    children = [
        _node(step, fallback_id=f"{pid}-p-{i}")
        for i, step in enumerate(steps)
        if isinstance(step, dict)
    ]
    if not children:
        return None
    return {
        "id": f"project-{pid}",
        "label": record.get("name", ""),
        "status": "done" if record.get("completed") else "open",
        "children": children,
    }


def _node(step: dict, fallback_id: str) -> dict:
    """One node and everything under it. Stored nodes always have an
    id; the fallback only covers very old records."""
    step_id = step.get("id") or fallback_id
    return {
        "id": str(step_id),
        "label": step.get("label") or "—",
        # Nothing writes `resolved` today, so every node shows "open".
        "status": "done" if step.get("resolved") else "open",
        "children": [
            _node(child, fallback_id=f"{step_id}-{j}")
            for j, child in enumerate(step.get("children") or [])
            if isinstance(child, dict)
        ],
    }
