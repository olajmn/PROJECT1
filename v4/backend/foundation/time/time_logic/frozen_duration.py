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
#      - TARGET_STEP_MINUTES
#      - MIN_STEPS
#      - MAX_STEPS
#      - _HORIZON_LENGTH_THRESHOLDS
#      - broadest_relevant_horizon()
#
#  4. Step planning
#      - step_count()
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

# Goal spans are broken into ~15-minute steps; MIN/MAX_STEPS bound
# that so a multi-day goal doesn't produce hundreds of steps and a
# 20-minute goal doesn't produce just one.
TARGET_STEP_MINUTES = 15
MIN_STEPS = 3
MAX_STEPS = 6


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


def step_count(duration: str | None) -> int | None:
    """
    How many steps `duration`'s span should be broken into -
    deterministic (see TARGET_STEP_MINUTES above), never the model's
    guess. None if `duration` doesn't resolve to a real span.
    """
    span = resolve_span(duration)
    if span is None:
        return None
    start, end = span
    total_minutes = (end - start).total_seconds() / 60
    raw_count = round(total_minutes / TARGET_STEP_MINUTES)
    return max(MIN_STEPS, min(MAX_STEPS, raw_count))


def step_plan(frozen: dict | None, steps: list[str] | None) -> list[dict] | None:
    """
    Zips stored step descriptions (the model's job - see
    step_generator.generate_steps()) with a deterministic time slice of
    the goal's frozen span, ready for the UI:
    [{"text", "start_label", "end_label"}, ...]. None if there are no
    steps or nothing frozen to slice.
    """
    if not steps:
        return None
    span = _span_from_frozen(frozen)
    if span is None:
        return None
    start, end = span
    count = len(steps)
    chunk = (end - start) / count
    spans = [(start + chunk * i, start + chunk * (i + 1)) for i in range(count)]
    result = []
    for (s, e), text in zip(spans, steps):
        same_day = s.date() == e.date()
        label_format = "%H:%M" if same_day else "%b %d"
        result.append({
            "text": text,
            "start_label": s.strftime(label_format),
            "end_label": e.strftime(label_format),
        })
    return result
