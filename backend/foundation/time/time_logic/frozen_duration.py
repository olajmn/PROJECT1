"""
The "frozen duration" lifecycle: everything computed ONCE when a goal
is created (see freeze_duration()) and then read back unchanged on
every later render, rather than re-resolved against the current moment
each time (see freeze_duration()'s docstring for the bug this fixes).
Builds on duration_resolution.py's resolve_span()/describe_duration() - nothing
here re-implements phrase matching itself.
"""

from datetime import datetime, timedelta

from backend.foundation.time.time_logic.duration_resolution import describe_duration, resolve_span


def freeze_duration(duration: str | None) -> dict | None:
    """
    Everything about `duration` that must be computed ONCE - at the
    moment a goal is created or its plan is replaced - and then stored
    and carried forward unchanged, never re-derived from "now" again.
    {"start": iso, "end": iso, "text": <description>}, or None if
    `duration` doesn't resolve to a real span at all (nothing to
    freeze - a same-day deadline or fully open text stays exactly as
    unresolved as describe_duration() already shows it).

    Fixes a real bug (2026-08-21): a forward-looking duration like
    "within the next 1 hour" was being re-resolved against the CURRENT
    moment on every single page render
    (duration_progress()/step_plan() used to take raw `duration` text
    and call resolve_span() fresh each time) - so its countdown quietly
    reset to a full hour on every refresh instead of counting down from
    when the goal was actually created. Calling this once at creation
    time (see backend/infrastructure/data_persistence.py's `save_plan(..., frozen_duration=...)`)
    and reading the stored result from then on is the fix - see
    duration_progress()/step_plan() below, which now take this dict
    instead of raw duration text.
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
    # whole-day spans (see resolve_span()'s docstring - that's what
    # gives a single-day span a non-zero width to draw) - shown as-is,
    # "2 days" would label its end "Aug 24" while describe_duration()
    # says "to 2026-08-23" right next to it, a real inconsistency.
    # Roll the LABEL back a day
    # whenever `end` lands exactly on a midnight boundary, so the two
    # numbers next to each other always agree - the bar's internal math
    # (`percent`) is unaffected, only this display string.
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


# A goal's resolved span divided into this many minutes per step is the
# concrete example that shaped this rule (2026-08-21): "1 hour" of
# grocery-shopping-and-cooking naturally breaks into about four ~15
# minute actions. MIN/MAX_STEPS keep that same target sane at the
# extremes a fixed 15-minute chunk wouldn't handle well on its own - a
# "this week" or "in March" goal would otherwise produce hundreds of
# steps, and a 20-minute goal would produce just one.
TARGET_STEP_MINUTES = 15
MIN_STEPS = 3
MAX_STEPS = 6


# Which PLAN_KEYS horizon is the broadest one worth filling in, given
# a goal's actual resolved length - a goal given "3 months" has no
# honest one_year answer, only up through one_month. Checked broadest
# to narrowest, first threshold cleared wins. Deliberately coarse
# buckets (a "month" close enough to 30 days, not read from
# backend.foundation.time.time_data.time_units.AVERAGE_DAYS_PER_MONTH) rather than a precise
# formula - same convention-over-precision trade WEEKS_PER_MONTH=4
# already makes elsewhere in this module; the actual question here
# ("is this goal roughly year-scale, month-scale, ...") doesn't need
# more precision than that. Added 2026-08-23, replacing two earlier,
# worse answers tried the same night: the model guessing relevance
# itself (inconsistent - see docs/05-decisions.md) and always filling
# every horizon regardless of scope (concrete, realistic-sounding but
# fabricated content for horizons broader than what was actually asked
# for - e.g. a "3 months" goal getting a full one_year answer). Code
# decides the boundary; the model is just told
# where it is, nothing left to its own judgment.
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
    Zips stored step descriptions (the model's job - see backend/planning/plan.py's
    `_generate_steps()`) with a deterministically-computed time slice of
    the goal's frozen span (`freeze_duration()` - this module's job),
    ready for the UI to render as a plain list:
    [{"text", "start_label", "end_label"}, ...]. None if there are no
    stored steps or nothing frozen to slice.

    Takes the SAME frozen dict duration_progress() does (see its
    docstring for why raw duration text isn't used here either) - the
    parent span is divided evenly into `len(steps)` pieces, against the
    frozen start/end rather than a fresh resolve_span() call (there
    used to be a separate step_spans(duration) doing this same division
    against a freshly-resolved span - removed 2026-08-21 once nothing
    called it any more; this function's own arithmetic below replaced
    it when steps moved to reading the frozen span instead).
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
