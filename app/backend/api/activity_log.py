"""
The activity log shown in Settings → Logs: every saved change across
all projects, newest first.

Nothing is recorded for the log. Every chat message and map change is
already saved as a timestamped line in data/plans.jsonl; this file
reads those lines and labels each one (Created / Chat / Map / Owner /
Cancelled).
"""

from backend.store.data_persistence import load_history, record_project_id
from backend.project.panes.create.resolver import created_at_key, get_latest_for_all_goals

# Newest entries shown; the rest stay in plans.jsonl.
LOG_LIMIT = 200
_LOG_TEXT_MAX = 160

# What each kind of saved change writes into `feedback` (see the
# save_plan() callers in project/panes/). Checked in this order.
_MAP_PREFIXES = ("Added step", "Imported ", "Removed step:", "Zoomed into:")
_OWNER_PREFIXES = ("Added to Vision", "Moved to Vision", "Removed from Vision")


def activity_log() -> list[dict]:
    """Every saved change across all projects, newest first:
    [{at, project_id, project, kind, text}].

    Read from plans.jsonl, where each change is already a timestamped
    record - nothing extra is recorded for the log. Renames overwrite
    the name in place instead of adding a record, so they never
    appear; `project` is each project's current name."""
    names = {
        record_project_id(r): r.get("goal") or ""
        for r in get_latest_for_all_goals()
    }
    records = sorted(load_history(), key=created_at_key, reverse=True)
    entries = []
    for record in records[:LOG_LIMIT]:
        pid = record_project_id(record)
        kind, text = _log_kind(record.get("feedback"))
        if len(text) > _LOG_TEXT_MAX:
            text = text[:_LOG_TEXT_MAX] + "…"
        entries.append({
            "at": record.get("created_at"),
            "project_id": pid,
            "project": names.get(pid) or record.get("goal") or "",
            "kind": kind,
            "text": text,
        })
    return entries


def _log_kind(feedback: str | None) -> tuple[str, str]:
    """(kind, text) for one saved change, read from its `feedback`."""
    text = (feedback or "").strip()
    if not text:
        return "Created", ""
    if " Note: " in text:
        return "Chat", text.split(" Note: ", 1)[1]
    if text == "Cancelled":
        return "Cancelled", ""
    if text.startswith(_MAP_PREFIXES):
        return "Map", text
    if text.startswith(_OWNER_PREFIXES):
        return "Owner", text
    # Chat that added nodes under a selected node saves the raw message
    # (edit_map.suggest_progression_from_chat); older records may too.
    return "Chat", text
