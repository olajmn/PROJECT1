"""
The "frozen duration" lifecycle: everything computed ONCE when a goal
is created (see freeze_duration()) and read back unchanged on every
later render, rather than re-resolved against the current moment each
time. Builds on duration_resolution.py's resolve_span()/
describe_duration() - nothing here re-implements phrase matching.
"""

# Contents
#  1. Duration freezing
#      - freeze_duration()
#      - _span_from_frozen()
#
#  2. Progress
#      - duration_progress()
#
#  3. Horizon scoping
#      - _HORIZON_LENGTH_THRESHOLDS
#      - broadest_relevant_horizon()
#
#  4. Step planning
#      - week_windows()
#      - day_windows()
#      - step_plan()

from datetime import datetime, timedelta

from backend.foundation.time.time_logic import now as _now
from backend.foundation.time.time_logic.duration_resolution import describe_duration, resolve_span

# 1. Duration freezing


def freeze_duration(duration: str | None) -> dict | None:
    """
    Everything about `duration` that must be computed ONCE - at goal
    creation - and then stored and reused unchanged, never re-derived
    from "now" again. {"start": iso, "end": iso, "text": <description>},
    or None if `duration` doesn't resolve to a real span.

    Re-resolving a forward-looking duration like "within the next
    hour" on every render would reset its countdown to a full hour on
    refresh, instead of counting down from creation. duration_progress()/
    step_plan() take this frozen dict, never raw duration text.
    """
    span = resolve_span(duration)
    if span is None:
        return None
    start, end = span
    return {"start": start.isoformat(), "end": end.isoformat(), "text": describe_duration(duration)}


def _span_from_frozen(frozen: dict | None) -> tuple[datetime, datetime] | None:
    """Deserializes a freeze_duration() dict back into (start, end)
    datetimes, or None if there's nothing frozen to read."""
    if not frozen:
        return None
    return datetime.fromisoformat(frozen["start"]), datetime.fromisoformat(frozen["end"])


# 2. Progress


def duration_progress(frozen: dict | None) -> dict | None:
    """
    A ready-to-render dict for a start/now/end progress bar - `percent`
    (0-100), `status` ("upcoming"/"active"/"overdue"), and
    `start_label`/`end_label` (HH:MM if same-day, else a date) - or
    None if there's nothing frozen to read.

    Takes a freeze_duration() dict, not raw duration text - only `now`
    is read live; start/end stay fixed (see freeze_duration()).
    """
    span = _span_from_frozen(frozen)
    if span is None:
        return None
    start, end = span
    now = _now()
    total = (end - start).total_seconds()
    if total <= 0:
        return None  # pragma: no cover - defensive; no resolver produces start >= end
    elapsed = (now - start).total_seconds()
    percent = elapsed / total * 100
    if now < start:
        status = "upcoming"
    elif now > end:
        status = "overdue"
    else:
        status = "active"
    same_day = start.date() == end.date()
    label_format = "%H:%M" if same_day else "%b %d"
    # `end` is midnight of the day AFTER the span's real last day for
    # whole-day spans (see resolve_span()'s docstring). Shown as-is,
    # "2 days" would label its end "Aug 24" while describe_duration()
    # says "to 2026-08-23" right next to it - roll the LABEL back a day
    # whenever `end` lands on a midnight boundary so the two agree; the
    # bar's internal math (`percent`) is unaffected, only this string.
    end_label_dt = end - timedelta(days=1) if end.time() == datetime.min.time() else end
    return {
        # Rounded to 2 decimals - not for display prettiness, but
        # because a raw float this size (e.g. 2.77e-08 for "just
        # started") renders in a CSS `style="left: ...%"` as scientific
        # notation, which isn't a valid CSS percentage.
        "percent": round(max(0, min(100, percent)), 2),
        "status": status,
        "start_label": start.strftime(label_format),
        "end_label": end_label_dt.strftime(label_format),
        # Raw ISO end timestamp for a client-side JS countdown, so the
        # UI doesn't have to poll the server every second. Naive/local
        # like the rest of this module - safe here since this is a
        # personal local-only dev tool (see backend/README.md).
        "end_iso": end.isoformat(),
    }


# 3. Horizon scoping

# Broadest PLAN_KEYS horizon worth filling, given a goal's resolved
# length, checked broadest to narrowest - first threshold cleared
# wins. Deliberately coarse buckets (a "month" ~= 30 days); code
# decides the boundary rather than the model guessing it - see
# docs/05-decisions.md.
_HORIZON_LENGTH_THRESHOLDS = (
    ("year", 300),
    ("month", 25),
    ("week", 5),
    ("today", 1),
    ("hour", 1 / 24),
    ("minute", 0),
)


def broadest_relevant_horizon(duration: str | None) -> str:
    """
    The PLAN_KEYS name of the broadest horizon worth filling in for
    `duration` (see _HORIZON_LENGTH_THRESHOLDS above), or "now"
    if `duration` doesn't resolve to a real span at all.
    """
    span = resolve_span(duration)
    if span is None:
        return "now"
    start, end = span
    total_days = (end - start).total_seconds() / 86400
    for horizon, min_days in _HORIZON_LENGTH_THRESHOLDS:
        if total_days >= min_days:
            return horizon
    return "now"  # pragma: no cover - defensive; the 0-day threshold above already catches everything


# 4. Step planning

# Week-grain skeleton: spans from the week horizon up to (but not
# including) the year horizon. Below that, a session still owns its
# own step list; at year scale the grain is years, not weeks - not
# built here yet. Thresholds match _HORIZON_LENGTH_THRESHOLDS above.
WEEK_GRAIN_MIN_DAYS = 5
WEEK_GRAIN_MAX_DAYS = 300
# A full week face has seven calendar days. A day may be empty or
# "off"; the last week of a span may hold the remaining calendar days
# (sometimes more than seven) so the month is not silently truncated.
DAYS_PER_WEEK = 7


def _window_labels(start: datetime, end: datetime) -> tuple[str, str]:
    """Display labels for one window. Whole-day exclusive midnights
    roll the end label back one day - same rule as duration_progress()."""
    same_day = start.date() == end.date()
    label_format = "%H:%M" if same_day else "%b %d"
    end_label_dt = end - timedelta(days=1) if end.time() == datetime.min.time() else end
    return start.strftime(label_format), end_label_dt.strftime(label_format)


def _inclusive_last_date(start: datetime, end: datetime):
    """Last calendar date belonging to [start, end). Exclusive midnight
    ends roll back one day - same convention as duration_progress()."""
    if end.time() == datetime.min.time():
        last = end.date() - timedelta(days=1)
    else:
        last = end.date()
    if last < start.date():
        return start.date()
    return last


def week_windows(frozen: dict | None) -> list[dict] | None:
    """
    The mechanical week-grain skeleton for a frozen span: N abutting
    calendar-week blocks covering start..end, where N is
    round(calendar_days / 7) (at least 1). Each full block is seven
    calendar days; the last block runs through the span's last day so
    leftover days of a ~month are not dropped.

    Each entry is {"start", "end", "start_label", "end_label"} - midnight
    ISO bounds (end exclusive) plus display labels.

    None when there is nothing frozen, or when the span is outside
    week grain (shorter than a week, or year-scale and above).
    """
    span = _span_from_frozen(frozen)
    if span is None:
        return None
    start, end = span
    start_d = start.date()
    end_d = _inclusive_last_date(start, end)
    total_days = (end_d - start_d).days + 1
    if total_days < WEEK_GRAIN_MIN_DAYS or total_days >= WEEK_GRAIN_MAX_DAYS:
        return None
    n = max(1, round(total_days / 7))
    windows = []
    for i in range(n):
        ws = start_d + timedelta(days=i * DAYS_PER_WEEK)
        if ws > end_d:
            break
        if i < n - 1:
            we = ws + timedelta(days=DAYS_PER_WEEK - 1)
            if we > end_d:
                we = end_d
        else:
            we = end_d
        s = datetime.combine(ws, datetime.min.time())
        e = datetime.combine(we + timedelta(days=1), datetime.min.time())
        start_label, end_label = _window_labels(s, e)
        windows.append({
            "start": s.isoformat(),
            "end": e.isoformat(),
            "start_label": start_label,
            "end_label": end_label,
        })
    return windows or None


def day_windows(week: dict) -> list[dict]:
    """
    One day candle per calendar day in a week window - consecutive
    dates, never equal time-slices (which skipped weekdays when the
    week was not exactly 7×24h).

    A normal week has DAYS_PER_WEEK days. A short last week is padded
    up to seven so the face stays complete (extra days can be "off").
    A long last week (remainder of the month) keeps every calendar day
    in range so nothing at the end of the span is dropped.

    `week` must have ISO "start"/"end". Raises ValueError if missing.
    """
    try:
        start = datetime.fromisoformat(week["start"])
        end = datetime.fromisoformat(week["end"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"week window needs ISO start/end: {week!r}") from e
    start_d = start.date()
    last_d = _inclusive_last_date(start, end)
    dates = []
    d = start_d
    while d <= last_d:
        dates.append(d)
        d += timedelta(days=1)
    while len(dates) < DAYS_PER_WEEK:
        dates.append(dates[-1] + timedelta(days=1) if dates else start_d)
    days = []
    for d in dates:
        s = datetime.combine(d, datetime.min.time())
        e = datetime.combine(d + timedelta(days=1), datetime.min.time())
        day_label = s.strftime("%a %b %d")
        days.append({
            "start": s.isoformat(),
            "end": e.isoformat(),
            "start_label": day_label,
            "end_label": day_label,
        })
    return days


def step_plan(frozen: dict | None, steps: list[str] | None) -> list[dict] | None:
    """
    Zips stored step descriptions with time labels for the UI:
    [{"text", "start_label", "end_label"}, ...].

    When every step dict already carries start_label/end_label (the
    week-grain path - dates decided by week_windows(), not invented
    here), those labels are used as-is. Otherwise falls back to an
    even slice of the frozen span across however many step texts were
    given - the older session-grain path, where count still comes from
    Planning and this module only paints the clock.

    `steps` may be plain label strings or dicts with a "label" key
    (and optional start_label/end_label). None if there are no steps
    or nothing frozen to read for the even-slice fallback.
    """
    if not steps:
        return None

    texts: list[str] = []
    dated: list[tuple[str, str] | None] = []
    for step in steps:
        if isinstance(step, dict):
            texts.append(step.get("label") or "")
            sl, el = step.get("start_label"), step.get("end_label")
            dated.append((sl, el) if isinstance(sl, str) and isinstance(el, str) else None)
        else:
            texts.append(step)
            dated.append(None)

    if dated and all(d is not None for d in dated):
        return [
            {"text": text, "start_label": d[0], "end_label": d[1]}
            for text, d in zip(texts, dated)
        ]

    span = _span_from_frozen(frozen)
    if span is None:
        return None
    start, end = span
    count = len(texts)
    chunk = (end - start) / count
    spans = [(start + chunk * i, start + chunk * (i + 1)) for i in range(count)]
    result = []
    for (s, e), text in zip(spans, texts):
        start_label, end_label = _window_labels(s, e)
        result.append({
            "text": text,
            "start_label": start_label,
            "end_label": end_label,
        })
    return result
