"""
A project's status: where it stands now (summary) and what has happened
(history, newest first). Summary facts come from the current SoT;
history lines come from the events tape — no model, nothing saved —
so it can never disagree with them.

The same status is shown above the chat (build_status(), for the screen)
and given to the chat's model (status_text()), so what the user sees is
what the model knows. docs/05-decisions.md #36–37, #41.
"""

# Contents
#  1. Settings
#      - HISTORY_LINES / TOP_LEVEL_SHOWN
#  2. The status
#      - build_status()
#      - status_text()
#  3. Summary facts
#      - _summary()
#      - _map_size()

from datetime import datetime

from backend.project.timeline import to_event
from backend.project.status.group_events import group_events, line_text


# ============================================================
# 1. Settings
# ============================================================

# History lines kept, newest first; older ones are only counted. Bounds
# the model's prompt as the project grows.
HISTORY_LINES = 25

# Top-level node names listed in the summary before "+N more".
TOP_LEVEL_SHOWN = 8

_MAP_EVENTS = ("node_added", "pasted", "folder_added", "suggested")


# ============================================================
# 2. The status
# ============================================================


def build_status(
    history: list[dict],
    now: datetime | None = None,
    current: dict | None = None,
) -> dict:
    """{summary: [{label, text, nodes}], history: [{day, time, text,
    nodes}], earlier: int} for one project's events, oldest first.
    `current` is the SoT record (map/name/owner); when omitted, the
    last history line is used (tests / older callers that still embed
    the map). `now` is only for tests; it decides what counts as today."""
    if not history:
        return {"summary": [], "history": [], "earlier": 0}
    now = now or datetime.now().astimezone()
    latest = current if current is not None else history[-1]
    name = latest.get("name") or history[-1].get("name") or "untitled"
    events = [to_event(record, name) for record in history]
    lines = group_events(events)

    shown = []
    for line in reversed(lines[-HISTORY_LINES:]):
        text, nodes = line_text(line)
        shown.append({
            "day": _day(line["when"], now),
            "time": line["when"].strftime("%H:%M") if line["when"] else "",
            "text": text,
            "nodes": nodes,
        })
    return {
        "summary": _summary(lines, now, latest),
        "history": shown,
        "earlier": max(0, len(lines) - HISTORY_LINES),
    }


def status_text(status: dict) -> str:
    """The same status as plain text, for the chat's model. Every history
    line carries its own day: with the day only as a heading above a
    group, the model placed yesterday's changes under today."""
    if not status["summary"]:
        return ""
    parts = [f"{row['label']}: {row['text']}" for row in status["summary"]]
    parts.append("")
    parts.append("History (newest first):")
    for line in status["history"]:
        parts.append(f"  {line['day']} {line['time']} — {line['text']}")
    if status["earlier"]:
        parts.append(f"  … {status['earlier']} earlier")
    return "\n".join(parts)


# ============================================================
# 3. Summary facts
# ============================================================


def _summary(
    lines: list[dict],
    now: datetime,
    latest: dict,
) -> list[dict]:
    rows = []

    project = latest.get("name") or "untitled"
    owner = latest.get("sim_user_id")
    first = next((line["when"] for line in lines if line["when"]), None)
    started = f", started {_date(first, now)}" if first else ""
    archived = " — archived" if latest.get("cancelled") else ""
    rows.append(_row("Project", f"{project}{f' (id#{owner})' if owner else ''}{started}{archived}"))

    last = lines[-1]["when"] if lines else None
    if last:
        rows.append(_row("Last change", f"{_day(last, now)} {last:%H:%M}"))

    steps = ((latest.get("plan") or {}).get("progression") or {}).get("steps") or []
    count, depth = _map_size(steps)
    if count:
        tops = [s.get("label") or "—" for s in steps if isinstance(s, dict)]
        more = f" +{len(tops) - TOP_LEVEL_SHOWN} more" if len(tops) > TOP_LEVEL_SHOWN else ""
        levels = "level" if depth == 1 else "levels"
        rows.append(_row("Map", f"{count} nodes, {depth} {levels}"))
        rows.append(_row("Top level", ", ".join(tops[:TOP_LEVEL_SHOWN]) + more, tops[:TOP_LEVEL_SHOWN]))
    else:
        rows.append(_row("Map", "empty"))

    recent: list[str] = []
    for line in reversed(lines):
        if line["event"] in _MAP_EVENTS:
            where = line.get("parent") or (line.get("label") if line["event"] == "suggested" else None)
            if where and where not in recent:
                recent.append(where)
        if len(recent) == 3:
            break
    if recent:
        rows.append(_row("Recent map work under", ", ".join(recent), recent))

    chats = [line for line in lines if line["event"] in ("chat", "chat_added_nodes")]
    if chats:
        focus = chats[-1].get("focus")
        rows.append(_row("Last talked about", focus or "the project as a whole", [focus] if focus else []))
    return rows


def _map_size(steps: list) -> tuple[int, int]:
    """(node count, depth) of the stored map."""
    count, depth = 0, 0
    stack = [(s, 1) for s in steps if isinstance(s, dict)]
    while stack:
        step, level = stack.pop()
        count += 1
        depth = max(depth, level)
        stack.extend((c, level + 1) for c in step.get("children") or [] if isinstance(c, dict))
    return count, depth


def _row(label: str, text: str, nodes: list[str] | None = None) -> dict:
    return {"label": label, "text": text, "nodes": nodes or []}


def _day(when: datetime | None, now: datetime) -> str:
    """"Today", "Yesterday", or a date."""
    if when is None:
        return "Unknown time"
    days = (now.date() - when.date()).days
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    return _date(when, now)


def _date(when: datetime, now: datetime) -> str:
    """"25 Sep", with the year when it is not this year."""
    return f"{when.day} {when:%b}" + ("" if when.year == now.year else f" {when.year}")
