"""
A project's status: where it stands now (summary) and a day-by-day
change pulse (history). Summary facts come from the current SoT;
the pulse counts non-chat events per calendar day — no model, nothing
saved — so it can never disagree with the tape.

Shown in the UI as the **Current state** panel (`build_status()`) and
given to the chat's model (`status_text()`, `recent_changes_text()`). docs/05-decisions.md #36–37, #41.
"""

# Contents
#  1. Settings
#      - HISTORY_DAYS / RECENT_CHANGES
#      - _CHAT_EVENTS
#  2. The status
#      - build_status()
#      - status_text()
#      - recent_changes_text()
#  3. Summary facts / day pulse
#      - _summary() / _change_pulse() / _map_size()

from collections import Counter
from datetime import datetime, timedelta

from backend.project.node import steps_of
from backend.project.timeline import to_event


# ============================================================
# 1. Settings
# ============================================================

# Calendar days kept in the change pulse, newest first. Older days are
# only counted in `earlier`.
HISTORY_DAYS = 25

# Individual changes the chat's model is told about, newest first. The
# day pulse only counts them; this says what each one was.
RECENT_CHANGES = 10

# Talk lines are not "changes" in the Status pulse (map/work only).
_CHAT_EVENTS = frozenset({"chat", "chat_added_nodes"})


# ============================================================
# 2. The status
# ============================================================


def build_status(
    history: list[dict],
    now: datetime | None = None,
    current: dict | None = None,
) -> dict:
    """{summary: [{label, text, nodes}], history: [{day, time, text,
    nodes, changes}], earlier: int} for one project's events, oldest
    first on disk. `history` here is one row per calendar day (change
    count; chat excluded). `current` is the SoT record; when omitted,
    the last history line is used. `now` is only for tests."""
    if not history:
        return {"summary": [], "history": [], "earlier": 0}
    now = now or datetime.now().astimezone()
    latest = current if current is not None else history[-1]
    name = latest.get("name") or history[-1].get("name") or "untitled"
    events = [to_event(record, name) for record in history]
    work = [e for e in events if e.get("event") not in _CHAT_EVENTS]
    pulse, earlier = _change_pulse(work, now)
    return {
        "summary": _summary(work, now, latest),
        "history": pulse,
        "earlier": earlier,
    }


def status_text(status: dict) -> str:
    """The summary rows as plain text, for the chat's model. The day
    pulse is left out: the model gets the changes themselves from
    recent_changes_text(), and a count beside the list read as more
    changes."""
    return "\n".join(f"{row['label']}: {row['text']}" for row in status["summary"])


def recent_changes_text(
    history: list[dict],
    now: datetime | None = None,
    limit: int = RECENT_CHANGES,
) -> str:
    """The last `limit` non-chat changes as plain text, newest first,
    for the chat's model. Empty when there are none. Chat turns are left
    out: the model already gets them as the conversation."""
    now = now or datetime.now().astimezone()
    events = [to_event(record, "") for record in history]
    work = [e for e in events if e.get("event") not in _CHAT_EVENTS][-limit:]
    if not work:
        return ""
    lines = ["Recent changes (newest first):"]
    for event in reversed(work):
        when = _event_when(event.get("at"))
        stamp = f"{_day(when, now)} {when:%H:%M}" if when else _day(None, now)
        lines.append(f"  {stamp} — {event.get('text') or event.get('kind')}")
    return "\n".join(lines)


# ============================================================
# 3. Summary facts / day pulse
# ============================================================


def _change_pulse(
    work_events: list[dict],
    now: datetime,
) -> tuple[list[dict], int]:
    """One row per calendar day from first change through today.

    Count = number of non-chat events that day (one save = one change).
    Quiet days are included as 0. Newest first; trim to HISTORY_DAYS.
    """
    counts: Counter = Counter()
    for event in work_events:
        when = _event_when(event.get("at"))
        if when is not None:
            counts[when.date()] += 1
    if not counts:
        return [], 0

    start = min(counts)
    end = now.date()
    if end < start:
        end = start

    days: list = []
    day = start
    while day <= end:
        days.append(day)
        day += timedelta(days=1)

    earlier = max(0, len(days) - HISTORY_DAYS)
    shown_dates = list(reversed(days[-HISTORY_DAYS:]))
    pulse = []
    for d in shown_dates:
        n = counts.get(d, 0)
        when = datetime(d.year, d.month, d.day, tzinfo=now.tzinfo)
        pulse.append({
            "day": _day(when, now),
            "time": "",
            "text": "1 change" if n == 1 else f"{n} changes",
            "nodes": [],
            "changes": n,
        })
    return pulse, earlier


def _summary(
    work_events: list[dict],
    now: datetime,
    latest: dict,
) -> list[dict]:
    rows = []

    project = latest.get("name") or "untitled"
    first = next(
        (w for e in work_events if (w := _event_when(e.get("at"))) is not None),
        None,
    )
    started = f", started {_date(first, now)}" if first else ""
    archived = " — archived" if latest.get("cancelled") else ""
    rows.append(_row("Project", f"{project}{started}{archived}"))

    last = None
    for event in work_events:
        when = _event_when(event.get("at"))
        if when is not None:
            last = when
    if last:
        rows.append(_row("Last change", f"{_day(last, now)} {last:%H:%M}"))

    steps = steps_of(latest)
    count, depth = _map_size(steps)
    if count:
        levels = "level" if depth == 1 else "levels"
        rows.append(_row("Map", f"{count} nodes, {depth} {levels}"))
    else:
        rows.append(_row("Map", "empty"))
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


def _event_when(at: str | None) -> datetime | None:
    """A saved event time as local time."""
    if not at:
        return None
    try:
        parsed = datetime.fromisoformat(at)
    except ValueError:
        return None
    return parsed.astimezone()


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
