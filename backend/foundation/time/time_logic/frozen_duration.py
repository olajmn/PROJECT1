"""
Frozen Duration
===============

The "frozen duration" lifecycle: everything computed ONCE when a goal
is created (see freeze_duration()) and read back unchanged on every
later render, rather than re-resolved against the current moment each
time. Builds on duration_resolution.py's resolve_span()/
describe_duration() - nothing here re-implements phrase matching.

Contents
1. Freezing a duration
2. Progress bar
3. Horizon scoping
4. Step planning
"""

from datetime import datetime, timedelta

from backend.foundation.time.time_logic.duration_resolution import describe_duration, resolve_span

# ============================================================
# 1. Freezing a duration
# ============================================================


def freeze_duration(duration: str | None) -> dict | None:
    """
    Everything about `duration` that must be computed ONCE - at the
    moment a goal is created or its plan is replaced - and then stored
    and carried forward unchanged, never re-derived from "now" again.
    {"start": iso, "end": iso, "text": <description>}, or None if
    `duration` doesn't resolve to a real span at all (nothing to
    freeze - a same-day deadline or fully open text stays exactly as
    unresolved as describe_duration() already shows it).

    Re-resolving a forward-looking duration like "within the next 1
    hour" against the CURRENT moment on every render would silently
    reset its countdown to a full hour on every refresh, instead of
    counting down from when the goal was actually created. Calling
    this once at creation time (see data_persistence.save_plan()'s
    `frozen_duration` parameter) and reading the stored result from
    then on is the fix - duration_progress()/step_plan() below take
    this dict, never raw duration text.
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


# ============================================================
# 2. Progress bar
# ============================================================


def duration_progress(frozen: dict | None) -> dict | None:
    """
    A ready-to-render dict for a start/now/end progress bar - `percent`
    (0-100, how far `now` sits between start and end), `status`
    ("upcoming"/"active"/"overdue" - `now` before/within/after the
    span), and `start_label`/`end_label` (HH:MM if the span is same-day,
    else a date) - or None if there's nothing frozen to read (see
    freeze_duration()).

    Takes an already-frozen `freeze_duration()` dict, NOT raw duration
    text - `start`/`end` must stay fixed across renders (see
    freeze_duration()'s docstring for why); only `now` below is ever
    read live, since the whole point of a progress bar is showing real
    elapsed time against a fixed target.

    `percent` is NOT clamped to 0-100 in `status` terms - "overdue"
    still gets a real (>100) percent internally so the template can
    decide how to show it (e.g. a full bar plus an explicit "overdue"
    label), rather than silently drawing an "active"-looking bar for a
    span that's already over.
    """
    span = _span_from_frozen(frozen)
    if span is None:
        return None
    start, end = span
    now = datetime.now()
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
        # Raw ISO timestamp (naive, local time - matches datetime.now()
        # everywhere else in this module) for the live countdown in the
        # UI to count down to client-side, in JS, without polling the
        # server every second. Local time on both ends is a safe
        # assumption here specifically because this is a personal
        # local-only dev tool (see backend/README.md) - server and
        # browser are always the same machine/timezone.
        "end_iso": end.isoformat(),
    }


# ============================================================
# 3. Horizon scoping
# ============================================================

# Target: a goal's resolved span divided into ~15-minute steps (e.g.
# "1 hour" of grocery-shopping-and-cooking breaks into about four).
# MIN/MAX_STEPS keep that sane at the extremes a fixed chunk size
# wouldn't handle well alone - a "this week" goal would otherwise
# produce hundreds of steps, a 20-minute goal just one.
TARGET_STEP_MINUTES = 15
MIN_STEPS = 3
MAX_STEPS = 6


# Which PLAN_KEYS horizon is the broadest one worth filling in, given
# a goal's actual resolved length - a goal given "3 months" has no
# honest one_year answer, only up through one_month. Checked broadest
# to narrowest, first threshold cleared wins. Deliberately coarse
# buckets (a "month" close enough to 30 days) rather than a precise
# calendar formula - the actual question here ("is this goal roughly
# year-scale, month-scale, ...") doesn't need more precision than
# that. Rejected alternatives (see
# docs/05-decisions.md): the model guessing relevance itself
# (inconsistent), and always filling every horizon regardless of scope
# (fabricates content for horizons broader than what was actually
# asked for - e.g. a full one_year answer for a "3 months" goal). Code
# decides the boundary; the model is just told where it is.
_HORIZON_LENGTH_THRESHOLDS = (
    ("one_year", 300),
    ("one_month", 25),
    ("this_week", 5),
    ("today", 1),
    ("this_hour", 1 / 24),
    ("this_minute", 0),
)


def broadest_relevant_horizon(duration: str | None) -> str:
    """
    The PLAN_KEYS name of the broadest horizon actually worth filling
    in for `duration` - see _HORIZON_LENGTH_THRESHOLDS above.
    "right_now" (the narrowest, always-filled one - see
    docs/02-product.md's "right_now is a trigger, not a time
    variable") if `duration` doesn't resolve to a real span at all -
    nothing grounded to measure, same honesty as every other
    "not parsed/verified by code" case in this module.
    """
    span = resolve_span(duration)
    if span is None:
        return "right_now"
    start, end = span
    total_days = (end - start).total_seconds() / 86400
    for horizon, min_days in _HORIZON_LENGTH_THRESHOLDS:
        if total_days >= min_days:
            return horizon
    return "right_now"  # pragma: no cover - defensive; the 0-day threshold above already catches everything


# ============================================================
# 4. Step planning
# ============================================================


def step_count(duration: str | None) -> int | None:
    """
    How many steps `duration`'s resolved span should be broken into -
    deterministic, not the model's guess (see TARGET_STEP_MINUTES
    above): the model's job is only ever to decide what each step IS,
    never how many there are or when they fall. None if `duration`
    doesn't resolve to a real span at all (see resolve_span()) - there
    is nothing grounded to divide, so no step count either, same
    honesty as every other "not parsed/verified by code" case in this
    module.
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
    Zips stored step descriptions (the model's job - see backend/goals/plan/step_generator.py's
    `generate_steps()`) with a deterministically-computed time slice of
    the goal's frozen span (`freeze_duration()` - this module's job),
    ready for the UI to render as a plain list:
    [{"text", "start_label", "end_label"}, ...]. None if there are no
    stored steps or nothing frozen to slice.

    Takes the SAME frozen dict duration_progress() does (see its
    docstring for why raw duration text isn't used here either) - the
    parent span is divided evenly into `len(steps)` pieces, against the
    frozen start/end rather than a fresh resolve_span() call.
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
