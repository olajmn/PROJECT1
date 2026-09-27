"""
Three parallel views over the same matched time phrase:
resolve_duration() for display text, resolve_span() for raw
(start, end) datetimes, describe_duration() for how it was
understood. All walk the same matchers in phrase_matching.py.
"""

# Contents
#  1. Formatting
#      - _format_date_range()
#
#  2. Duration resolution
#      - resolve_duration()
#
#  3. Span resolution
#      - resolve_span()
#
#  4. Duration description
#      - describe_duration()

from datetime import date, datetime, timedelta

from backend.foundation.time.time_logic import now as _now
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
    _matched_season_name,
    _matched_weekday_name,
    _month_name_range,
    _named_fraction_end,
    _season_range,
    _weekday_name_date,
)


# 1. Formatting


def _format_date_range(start_date: date, end_date: date) -> str:
    if start_date == end_date:
        return start_date.isoformat()
    return f"{start_date.isoformat()} to {end_date.isoformat()}"


# 2. Duration resolution


def resolve_duration(duration: str | None, hemisphere: str | None = None) -> str | None:
    """
    Human-readable description with the resolution appended, or
    `duration` unchanged if nothing matched.

    `hemisphere` ("northern"/"southern") only matters for a recognized
    season phrase ("this summer" etc.) - every other matcher is
    hemisphere-independent. None (the default, and the only value any
    current caller passes - this project has no location/hemisphere
    concept yet) means a season is reported as recognized but not
    resolved, never guessed (see _matched_season_name()/_season_range()).
    """
    if not duration:
        return duration

    day_match = _matched_day_segment(duration)
    if day_match is not None:
        word, (start, end) = day_match
        target_date = _now().date() + timedelta(days=_matched_day_offset(duration))
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

    season_match = _matched_season_name(duration)
    if season_match is not None:
        if hemisphere is None:
            return f"{duration} (recognized as a season - hemisphere unknown, not resolved)"
        season, prefix = season_match
        start_date, end_date = _season_range(season, hemisphere, prefix)
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
        now = _now()
        return f"{duration} (resolved: now {now.strftime('%H:%M')} -> {end.strftime('%Y-%m-%d %H:%M')})"

    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            now = _now()
            return f"{duration} (resolved: now {now.strftime('%H:%M')} -> {end_time.strftime('%Y-%m-%d %H:%M')})"
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            today = _now().date()
            return f"{duration} (resolved: {today.isoformat()} to {end_date.isoformat()})"

    return duration


# 3. Span resolution


def resolve_span(duration: str | None, hemisphere: str | None = None) -> tuple[datetime, datetime] | None:
    """
    The (start, end) datetime span `duration` resolves to, or None
    if nothing grounds it in a real start and end. `start` is `now`
    for any forward-looking span (clock times, lengths, etc.); `end`
    is next-day midnight for whole-day ranges.

    `hemisphere` - see resolve_duration()'s docstring. A season with no
    `hemisphere` given resolves to None here, same as anything else
    not grounded in a real span - never a guessed hemisphere.
    """
    if not duration:
        return None

    day_match = _matched_day_segment(duration)
    if day_match is not None:
        _, (start_hour, end_hour) = day_match
        target_date = _now().date() + timedelta(days=_matched_day_offset(duration))
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
        return _now(), _clock_time_date(duration, hour, minute)

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

    season_match = _matched_season_name(duration)
    if season_match is not None:
        if hemisphere is None:
            return None
        season, prefix = season_match
        start_date, end_date = _season_range(season, hemisphere, prefix)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        return start_dt, end_dt

    weekday_match = _matched_weekday_name(duration)
    if weekday_match is not None:
        _, number, prefix = weekday_match
        target_date = _weekday_name_date(number, prefix)
        return _now(), datetime.combine(target_date + timedelta(days=1), datetime.min.time())

    fraction_match = _matched_named_fraction(duration)
    if fraction_match is not None:
        _, unit, value = fraction_match
        return _now(), _named_fraction_end(unit, value)

    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            return _now(), end_time
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            return _now(), datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    return None


# 4. Duration description


def describe_duration(duration: str | None, hemisphere: str | None = None) -> str:
    """
    One-line explanation of how `duration` was understood - which
    matcher fired, or that none did - for display next to the raw text.

    `hemisphere` - see resolve_duration()'s docstring.
    """
    if not duration:
        return ""
    match = _matched_day_segment(duration)
    if match:
        word, (start, end) = match
        target_date = _now().date() + timedelta(days=_matched_day_offset(duration))
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
    season_match = _matched_season_name(duration)
    if season_match:
        season, prefix = season_match
        shown = f"{prefix} {season}" if prefix else season
        if hemisphere is None:
            return f'given, recognized as a season ("{shown}") - hemisphere unknown, not resolved'
        start_date, end_date = _season_range(season, hemisphere, prefix)
        return f'given, resolved by code: "{shown}" = {_format_date_range(start_date, end_date)}'
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
        now = _now().strftime("%H:%M")
        return f'given, resolved by code: "{shown}" = now {now} -> {end.strftime("%Y-%m-%d %H:%M")}'
    deadline = _matched_deadline_phrase(duration)
    if deadline:
        return f'given, recognized as a same-day deadline ("{deadline}") - actual time unknown, not grounded'
    length_match = _matched_length(duration)
    if length_match is not None:
        number, unit = length_match
        end_time = _length_end_time(number, unit)
        if end_time is not None:
            now = _now().strftime("%H:%M")
            return f'given, resolved by code: "{number} {unit}(s)" = now {now} -> {end_time.strftime("%Y-%m-%d %H:%M")}'
        end_date = _length_end_date(number, unit)
        if end_date is not None:
            today = _now().date().isoformat()
            return f'given, resolved by code: "{number} {unit}(s)" = {today} to {end_date.isoformat()}'
        return "given, recognized as a length, not grounded in a clock time"
    return "given, not parsed/verified by code"
