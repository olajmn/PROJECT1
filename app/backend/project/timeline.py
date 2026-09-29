"""
A project's timeline: every saved change, in order, as plain events —
created, chat, node added, renamed, archived, ...

Every change is already saved as one timestamped line in
data/projects/{id}/events.jsonl (storage/project_persistence.py). This file only reads
those lines back as events; it writes nothing. Used by Settings → Logs
(api/activity_log.py) and the project timeline address
(/api/projects/<id>/timeline). See docs/04-current-state.md § 2.
"""

# Contents
#  1. What happened
#      - GROUPS
#      - event_name()
#
#  2. Reading timelines
#      - project_timeline()
#      - all_events()
#      - to_event()

from backend.storage.project_persistence import (
    load_current,
    load_history,
    record_project_id,
)
from backend.project.panes.create.resolver import (
    created_at_key,
    get_history_for_project,
    get_latest_for_all_projects,
)


# ============================================================
# 1. What happened
# ============================================================

# Each saved line's `event` (written since 2026-09-25) → the group shown
# as the entry's title in Settings → Logs.
GROUPS = {
    "created": "Created",
    "chat": "Chat",
    "chat_added_nodes": "Chat",
    "node_added": "Map",
    "node_removed": "Map",
    "node_moved": "Map",
    "pasted": "Map",
    "folder_added": "Map",
    "tree_inserted": "Map",
    "suggested": "Map",
    "renamed": "Renamed",
    "owner_changed": "Owner",
    "archived": "Archived",
}

_TEXT_MAX = 160


def event_name(record: dict) -> str:
    """What this saved line was. Every line carries `event`; lines saved
    before it existed were given one by the 2026-09-27 conversion (#59)."""
    return record.get("event") or "other"


# ============================================================
# 2. Reading timelines
# ============================================================


def project_timeline(project_id: int) -> list[dict]:
    """One project's events, oldest first — its whole history."""
    history = get_history_for_project(project_id)
    current = load_current(project_id)
    name = (current or {}).get("name", "") or (
        history[-1].get("name", "") if history else ""
    )
    return [to_event(r, name) for r in history]


def all_events(limit: int | None = None, offset: int = 0) -> list[dict]:
    """Every project's events together, newest first; `offset` skips the
    newest ones already shown and `limit` keeps the next ones only."""
    names = {
        record_project_id(r): r.get("name") or ""
        for r in get_latest_for_all_projects()
    }
    records = sorted(load_history(), key=created_at_key, reverse=True)
    records = records[max(offset, 0):]
    if limit is not None:
        records = records[:limit]
    return [
        to_event(r, names.get(record_project_id(r)) or r.get("name") or "")
        for r in records
    ]


def to_event(record: dict, project_name: str) -> dict:
    """{at, project_id, project, event, kind, text, focus?} for one saved
    line. `project` is the project's current name; `text` is what a person
    would want to read: the chat message, or what changed; `focus` is the
    map node a chat message was about, when there was one."""
    name = event_name(record)
    feedback = (record.get("feedback") or "").strip()
    if name == "chat":
        text = feedback.split(" Note: ", 1)[-1]
    elif name in ("created", "archived"):
        text = ""
    else:
        text = feedback
    if len(text) > _TEXT_MAX:
        text = text[:_TEXT_MAX] + "…"
    event = {
        "at": record.get("created_at"),
        "project_id": record_project_id(record),
        "project": project_name,
        "event": name,
        "kind": GROUPS.get(name, "Other"),
        "text": text,
    }
    focus = (record.get("map_focus") or "").strip()
    if focus:
        event["focus"] = focus
    return event
