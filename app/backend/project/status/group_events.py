"""
Turns a project's events (project/timeline.py) into readable history
lines, collapsing runs of similar events into one:

    Added step under Design: Walls   ┐
    Added step under Design: Roof    ├─→  Added 3 nodes under "Design"
    Added step under Design: Doors   ┘

No model, no files: events in, lines out.
"""

# Contents
#  1. Reading one event
#      - parse_event()
#  2. Grouping
#      - group_events()
#      - line_text()

import re
from datetime import datetime

# Node names listed on one chat line before "+N".
_ABOUT_SHOWN = 3


# ============================================================
# 1. Reading one event
# ============================================================

# The fixed shapes each kind of change writes into `feedback`
# (project/panes/canvas/edit_map.py, create/rename.py).
_ADDED = re.compile(r"^Added step(?: under (?P<parent>.+?))?: (?P<label>.+)$")
_IMPORTED = re.compile(r"^Imported (?P<count>\d+) step\(s\)(?: under (?P<parent>.+))?$")
_REMOVED = re.compile(r"^Removed step: (?P<label>.+)$")
_SUGGESTED = re.compile(r"^Zoomed into: (?P<label>.+)$")
_RENAMED = re.compile(r"^Renamed: (?P<old>.*) → (?P<new>.*)$")


def parse_event(event: dict) -> dict:
    """The event plus what its text says: `label` (the node it is about),
    `parent`, `count` — whichever apply."""
    out = dict(event)
    text = event.get("text") or ""
    name = event.get("event")
    patterns = {
        "node_added": _ADDED,
        "pasted": _IMPORTED,
        "folder_added": _IMPORTED,
        "node_removed": _REMOVED,
        "suggested": _SUGGESTED,
        "renamed": _RENAMED,
    }
    match = patterns[name].match(text) if name in patterns else None
    if match:
        out.update({k: v for k, v in match.groupdict().items() if v is not None})
    return out


# ============================================================
# 2. Grouping
# ============================================================


def group_events(events: list[dict]) -> list[dict]:
    """Events oldest first → history lines oldest first:
    [{when, event, count, label?, parent?, focus?, labels}].

    Next to each other on the same day, these collapse into one line:
    nodes added under the same parent, nodes removed, and chat messages
    (collecting which nodes the chat was about)."""
    lines: list[dict] = []
    for raw in events:
        event = parse_event(raw)
        when = _local(event.get("at"))
        key = _group_key(event)
        last = lines[-1] if lines else None
        if (
            last is not None
            and key is not None
            and last["key"] == key
            and last["when"] is not None
            and when is not None
            and last["when"].date() == when.date()
        ):
            last["count"] += 1
            last["when"] = when
            if event.get("label"):
                last["labels"].append(event["label"])
            if event.get("focus") and event["focus"] not in last["focuses"]:
                last["focuses"].append(event["focus"])
            # The newest message decides what was talked about last.
            last["focus"] = event.get("focus")
            continue
        lines.append({
            "key": key,
            "when": when,
            "event": event["event"],
            "count": 1,
            "label": event.get("label"),
            "parent": event.get("parent"),
            "old": event.get("old"),
            "new": event.get("new"),
            "size": event.get("count"),
            "focus": event.get("focus"),
            "text": event.get("text") or "",
            "labels": [event["label"]] if event.get("label") else [],
            "focuses": [event["focus"]] if event.get("focus") else [],
        })
    for line in lines:
        del line["key"]
    return lines


def line_text(line: dict) -> tuple[str, list[str]]:
    """(what the line says, node names mentioned in it) for one history
    line. Node names are what the panel makes clickable."""
    name, count = line["event"], line["count"]
    parent, label = line.get("parent"), line.get("label")
    under = f' under "{parent}"' if parent else ""
    if name == "created":
        return "Created", []
    if name == "archived":
        return "Archived", []
    if name in ("chat", "chat_added_nodes"):
        noun = "message" if count == 1 else "messages"
        focuses = line.get("focuses") or []
        shown = focuses[:_ABOUT_SHOWN]
        more = f" +{len(focuses) - _ABOUT_SHOWN}" if len(focuses) > _ABOUT_SHOWN else ""
        about = (" about " + ", ".join(f'"{f}"' for f in shown) + more) if shown else ""
        return f"Chat · {count} {noun}{about}", shown
    if name == "node_added":
        if count == 1:
            return f'Added "{label}"{under}', [n for n in (label, parent) if n]
        return f"Added {count} nodes{under}", [parent] if parent else []
    if name == "node_removed":
        if count == 1:
            return f'Removed "{label}"', []
        return f"Removed {count} nodes", []
    if name in ("pasted", "folder_added"):
        # The saved count is top-level nodes only, not the whole tree.
        tops = line.get("size") or "?"
        noun = "top node" if tops == "1" else "top nodes"
        what = "Pasted structure" if name == "pasted" else "Added a folder"
        return f"{what} ({tops} {noun}){under}", [parent] if parent else []
    if name == "suggested":
        return f'Suggested children under "{label}"', [label] if label else []
    if name == "renamed":
        return f'Renamed "{line.get("old")}" → "{line.get("new")}"', []
    if name == "owner_changed":
        # Older lines still say "Vision", the earlier name for an id.
        return line["text"].replace("Vision", "id"), []
    return line["text"] or name, []


def _group_key(event: dict) -> tuple | None:
    """Events with the same key, next to each other, share one line.
    None means the event always stands alone."""
    name = event.get("event")
    if name in ("chat", "chat_added_nodes"):
        return ("chat",)
    if name == "node_added":
        return ("node_added", event.get("parent"))
    if name == "node_removed":
        return ("node_removed",)
    return None


def _local(at: str | None) -> datetime | None:
    """A saved time as local time. Times saved before 2026-09-25 have no
    offset and are already local; astimezone() treats them that way."""
    if not at:
        return None
    try:
        parsed = datetime.fromisoformat(at)
    except ValueError:
        return None
    return parsed.astimezone()
