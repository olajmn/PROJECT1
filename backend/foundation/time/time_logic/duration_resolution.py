"""
Three parallel "views" over the same matched time phrase, all walking
the matchers in phrase_matching.py in the same broadest-signal-first order:

- resolve_duration() - a human-readable description with the
  resolution appended, for showing next to the raw text in the UI.
- resolve_span() - the same resolution as a raw (start, end) datetime
  pair, for computing with (progress bars, step slicing - see
  frozen_duration.py) rather than displaying.
- describe_duration() - explains HOW something was understood (which
  matcher fired, or that nothing did), rather than what it resolved to.

Anything not recognized by any matcher is passed through unchanged, or
reported as unresolved - the model still has to interpret it itself,
same as before this file existed.
"""

from datetime import date, datetime, timedelta

from backend.foundation.time.time_logic.phrase_matching import (
    _clock_time_date,
    _length_end_date,
    _length_end_time,
    _matched_clock_time,
    _matched_day_offset,
    _matched_day_segment,
    _matched_deadline_phrase,
    _matched_length,
    _matched_month_name,
    _matched_named_fraction,
    _matched_period_phrase,
    _matched_weekday_name,
    _month_name_range,
    _named_fraction_end,
    _weekday_name_date,
)


def _format_date_range(start_date: date, end_date: date) -> str:
    """A single date on its own ("2026-08-22") when start and end are
    the same day (yesterday/today/tomorrow), "X to Y" otherwise."""
    if start_date == end_date:
        return start_date.isoformat()
    return f"{start_date.isoformat()} to {end_date.isoformat()}"


def resolve_duration(duration: str | None) -> str | None:
    """
    Ground `duration` in a real clock window or calendar date range when
    it's a recognized day segment (see DAY_SEGMENTS) or whole-period
    phrase (see PERIOD_PHRASES), so the model is told an actual range
    instead of just the word "evening" or "this month". Anything that
    isn't recognized - a plain length ("30 minutes") or fully open text
    ("before my trip") - is passed through unchanged; the model still
    has to interpret those itself, same as before.
    """
    if not duration:
        return duration

    day_match = _matched_day_segment(duration)
    if day_match is not None:
        word, (start, end) = day_match
        target_date = datetime.now().date() + timedelta(days=_matched_day_offset(duration))
        if start < end:
            window = f"{start:02d}:00-{end:02d}:00"
        else:
            window = f"{start:02d}:00-{end:02d}:00 (past midnight)"
        return f"{duration} (resolved: {target_date.isoformat()}, {window})"

    clock_match = _matched_clock_time(duration)
    if clock_match is not None:
        hour, minute = clock_match
        target = _clock_time_date(duration, hour, minute)
        return f"{duration} (resolved: {target.strftime('%Y-%m-%d %H:%M')})"

    period_match = _matched_period_phrase(duration)
    if period_match is not None:
        phrase, (start_date, end_date) = period_match
        return f"{duration} (resolved: {_format_date_range(start_date, end_date)})"

    month_match = _matched_month_name(duration)
    if month_match is not None:
        name, month = month_match
        start_date, end_date = _month_name_range(month)
        return f"{duration} (resolved: {_format_date_range(start_date, end_date)})"

    weekday_match = _matched_weekday_name(duration)
    if weekday_match is not None:
        name, number, prefix = weekday_match
        target_date = _weekday_name_date(number, prefix)
        return f"{duration} (resolved: {target_date.isoformat()})"

    fraction_match = _matched_named_fraction(duration)
    if fraction_match is not None:
        segment, unit, value = fraction_match
        end = _named_fraction_end(unit, value)
        now = datetime.now()
        return f"{duration} (resolved: now {now.strftime('%H:%M')} -> {end.strftime('%Y-%m-%d %H:%M')})"

    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            now = datetime.now()
            return f"{duration} (resolved: now {now.strftime('%H:%M')} -> {end_time.strftime('%Y-%m-%d %H:%M')})"
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            today = datetime.now().date()
            return f"{duration} (resolved: {today.isoformat()} to {end_date.isoformat()})"

    return duration


def resolve_span(duration: str | None) -> tuple[datetime, datetime] | None:
    """
    The actual (start, end) datetime span `duration` resolves to, for
    visualizing it (a start/now/end bar in the UI) - reuses the exact
    same matchers/resolvers resolve_duration()/describe_duration()
    already call, just returning raw datetimes instead of a formatted
    string, so there's no second copy of any date arithmetic. None for
    anything not grounded in a real start and end (a deadline with an
    unknown clock time, or fully unrecognized text) - nothing to draw a
    bar for, same honesty as the text form's "not parsed/verified" and
    "not grounded" cases.

    `start` is `now` for anything that's a forward-looking span from
    this moment (clock times, weekday names, named fractions, plain
    lengths) rather than some absolute start that doesn't exist - "1
    hour from now" is now -> now+1h, not a fabricated start point.
    `end` is the end of the last day (next day's midnight) for whole-
    day ranges (day segments' date, period phrases, month names,
    weekday names), so a single-day span still has a non-zero width to
    draw.
    """
    if not duration:
        return None

    day_match = _matched_day_segment(duration)
    if day_match is not None:
        _, (start_hour, end_hour) = day_match
        target_date = datetime.now().date() + timedelta(days=_matched_day_offset(duration))
        midnight = datetime.min.time()
        start_dt = datetime.combine(target_date, midnight.replace(hour=start_hour))
        if start_hour < end_hour:
            end_dt = datetime.combine(target_date, midnight.replace(hour=end_hour))
        else:
            end_dt = datetime.combine(target_date + timedelta(days=1), midnight.replace(hour=end_hour))
        return start_dt, end_dt

    clock_match = _matched_clock_time(duration)
    if clock_match is not None:
        hour, minute = clock_match
        return datetime.now(), _clock_time_date(duration, hour, minute)

    period_match = _matched_period_phrase(duration)
    if period_match is not None:
        _, (start_date, end_date) = period_match
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        return start_dt, end_dt

    month_match = _matched_month_name(duration)
    if month_match is not None:
        _, month = month_match
        start_date, end_date = _month_name_range(month)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        return start_dt, end_dt

    weekday_match = _matched_weekday_name(duration)
    if weekday_match is not None:
        _, number, prefix = weekday_match
        target_date = _weekday_name_date(number, prefix)
        return datetime.now(), datetime.combine(target_date + timedelta(days=1), datetime.min.time())

    fraction_match = _matched_named_fraction(duration)
    if fraction_match is not None:
        _, unit, value = fraction_match
        return datetime.now(), _named_fraction_end(unit, value)

    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            return datetime.now(), end_time
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            return datetime.now(), datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    return None


def describe_duration(duration: str | None) -> str:
    """
    One-line explanation of how `duration` was understood, for display
    next to it in the UI (see index.html / _plan_entry.html) - so it's
    visible whether the code actually grounded this in a real clock
    window (a day segment) or is just passing the raw text to the model
    unexamined (a length like "30 minutes", or fully open text).
    """
    if not duration:
        return ""
    match = _matched_day_segment(duration)
    if match:
        word, (start, end) = match
        target_date = datetime.now().date() + timedelta(days=_matched_day_offset(duration))
        return f'given, resolved by code: "{word}" = {target_date.isoformat()} {start:02d}:00-{end:02d}:00'
    clock_match = _matched_clock_time(duration)
    if clock_match is not None:
        hour, minute = clock_match
        target = _clock_time_date(duration, hour, minute)
        return f'given, resolved by code: clock time = {target.strftime("%Y-%m-%d %H:%M")}'
    period_match = _matched_period_phrase(duration)
    if period_match:
        phrase, (start_date, end_date) = period_match
        return f'given, resolved by code: "{phrase}" = {_format_date_range(start_date, end_date)}'
    month_match = _matched_month_name(duration)
    if month_match:
        name, month = month_match
        start_date, end_date = _month_name_range(month)
        return f'given, resolved by code: "{name}" = {_format_date_range(start_date, end_date)}'
    weekday_match = _matched_weekday_name(duration)
    if weekday_match:
        name, number, prefix = weekday_match
        target_date = _weekday_name_date(number, prefix)
        shown = f"{prefix} {name}" if prefix else name
        return f'given, resolved by code: "{shown}" = {target_date.isoformat()}'
    fraction_match = _matched_named_fraction(duration)
    if fraction_match:
        segment, unit, value = fraction_match
        end = _named_fraction_end(unit, value)
        shown = f"{segment} {unit}"
        now = datetime.now().strftime("%H:%M")
        return f'given, resolved by code: "{shown}" = now {now} -> {end.strftime("%Y-%m-%d %H:%M")}'
    deadline = _matched_deadline_phrase(duration)
    if deadline:
        return f'given, recognized as a same-day deadline ("{deadline}") - actual time unknown, not grounded'
    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            now = datetime.now().strftime("%H:%M")
            return f'given, resolved by code: "{number} {unit}(s)" = now {now} -> {end_time.strftime("%Y-%m-%d %H:%M")}'
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            today = datetime.now().date().isoformat()
            return f'given, resolved by code: "{number} {unit}(s)" = {today} to {end_date.isoformat()}'
        return "given, recognized as a length, not grounded in a clock time"
    return "given, not parsed/verified by code"
