"""
Finds known time phrases in free text and turns them into concrete
values (hours, dates, offsets), using the pattern tables in the
sibling time_data/ package. Matches and interprets only - deciding
how a match is used or described is duration_resolution.py's job.

extract_duration_phrase() below is the only function meant to be
called from outside this package - it returns the raw phrase text,
not a resolved description (see duration_resolution.resolve_duration()).
"""

# Contents
#  1. Shared matching helper
#      - _FRACTION_TABLES
#      - _contains_phrase()
#
#  2. Day segments & clock times
#      - _matched_day_segment()
#      - _matched_day_offset()
#      - _matched_clock_time()
#      - _clock_time_date()
#
#  3. Deadlines & calendar periods
#      - _matched_deadline_phrase()
#      - _add_months()
#      - _period_range()
#      - _matched_month_name()
#      - _month_name_range()
#      - _matched_weekday_name()
#      - _weekday_name_date()
#
#  4. Seasons
#      - _matched_season_name()
#      - _season_month_range()
#      - _season_occurrence()
#      - _season_range()
#
#  5. Named fractions & lengths
#      - _matched_named_fraction()
#      - _named_fraction_end()
#      - _matched_length()
#      - _length_end_date()
#      - _length_end_time()
#      - _matched_period_phrase()
#
#  6. Public entry point
#      - extract_duration_phrase()

import calendar
import re
from datetime import date, datetime, timedelta

from backend.foundation.time.time_logic import now as _now
from backend.foundation.time.time_data.time_segments import (
    CLOCK_12H_RE,
    CLOCK_24H_RE,
    DAY_FRACTIONS,
    DAY_SEGMENTS,
    DEADLINE_RE,
    DURATION_LENGTH_RE,
    HOUR_SEGMENTS,
    MINUTE_SEGMENTS,
    MONTH_NUMBERS,
    NAMED_FRACTION_RE,
    NORTHERN_SEASON_MONTHS,
    PERIOD_PHRASES,
    SEASON_ALIASES,
    SOUTHERN_SEASON_MONTHS,
    WEEKDAY_NUMBERS,
    WEEKDAY_PREFIXES,
)
from backend.foundation.time.time_data.time_units import (
    DAYS_PER_WEEK,
    MONTHS_PER_YEAR,
    YEARS_PER_CENTURY,
    YEARS_PER_DECADE,
    YEARS_PER_MILLENNIUM,
)

# Which table a NAMED_FRACTION_RE match's unit word belongs to - the
# single place that dispatch is decided, so _matched_named_fraction()
# doesn't need its own if/elif chain.
_FRACTION_TABLES = {
    "hour": HOUR_SEGMENTS,
    "minute": MINUTE_SEGMENTS,
    "day": DAY_FRACTIONS,
}


# 1. Shared matching helper


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Whether `phrase` (already lowercase) appears in `text` as whole
    word(s), not a substring - `"this week" in "this weekend"` would
    match wrongly under a plain substring check, same risk as a month
    name colliding with an everyday word (see _matched_month_name()).
    """
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


# 2. Day segments & clock times


def _matched_day_segment(duration: str) -> tuple[str, tuple[int, int]] | None:
    """Return (word, (start_hour, end_hour)) for the first known day
    segment found in `duration`, or None if none match."""
    lowered = duration.lower()
    for word, hours in DAY_SEGMENTS.items():
        if _contains_phrase(lowered, word):
            return word, hours
    return None


def _matched_day_offset(duration: str) -> int:
    """
    0 (today) by default, or the +/-N day offset if `duration` also
    names yesterday/today/tomorrow (see PERIOD_PHRASES' "day" entries) -
    lets a day segment combine with it correctly.

    Without this, "tomorrow evening" would resolve against today's
    date - DAY_SEGMENTS only knows clock hours, never which day they
    belong to.
    """
    lowered = duration.lower()
    for phrase, (unit, offset) in PERIOD_PHRASES.items():
        if unit == "day" and _contains_phrase(lowered, phrase):
            return offset
    return 0


def _matched_clock_time(duration: str) -> tuple[int, int] | None:
    """
    Return (hour, minute) in 24h form for a recognized literal clock
    time in `duration` - 12-hour ("1 o'clock", "3pm", "11:30am") or
    24-hour ("14:30") - or None if none match.

    A bare "o'clock" with no am/pm resolves to PM (see CLOCK_12H_RE in
    time_segments.py).
    """
    match = CLOCK_12H_RE.search(duration)
    if match:
        hour = int(match.group(1)) % 12
        minute = int(match.group(2) or 0)
        if match.group(3).lower() in ("pm", "o'clock"):
            hour += 12
        return hour, minute
    match = CLOCK_24H_RE.search(duration)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def _clock_time_date(duration: str, hour: int, minute: int) -> datetime:
    """
    The actual date+time a recognized clock time refers to - today's
    date, or tomorrow's/yesterday's if `duration` also names one (see
    _matched_day_offset()) - at that hour:minute. Same day-offset
    combination DAY_SEGMENTS already uses for "tomorrow evening".
    """
    target_date = _now().date() + timedelta(days=_matched_day_offset(duration))
    return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))


# 3. Deadlines & calendar periods


def _matched_deadline_phrase(duration: str) -> str | None:
    """Return the actual matched text if `duration` names a routine-
    event deadline (see time_segments.DEADLINE_RE), or None if none match."""
    match = DEADLINE_RE.search(duration)
    return match.group(0) if match else None


def _add_months(d: date, months: int) -> date:
    """d shifted by `months` calendar months, clamped to the last valid
    day of the target month (e.g. Jan 31 + 1 month -> Feb 28/29)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // MONTHS_PER_YEAR
    month = month_index % MONTHS_PER_YEAR + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _period_range(unit: str, offset: int) -> tuple[date, date]:
    """
    The actual (start, end) calendar date range "yesterday/today/
    tomorrow/last/this/next week/month/year" refers to, computed from
    today's real date - see time_segments.PERIOD_PHRASES. "day" returns
    a single-day range (that day, that day) - same offset arithmetic as
    every other unit, just a range of one.
    """
    today = _now().date()
    if unit == "day":
        d = today + timedelta(days=offset)
        return d, d
    if unit == "week":
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        return start, start + timedelta(days=DAYS_PER_WEEK - 1)
    if unit == "month":
        start = _add_months(today.replace(day=1), offset)
        return start, start.replace(day=calendar.monthrange(start.year, start.month)[1])
    if unit == "year":
        year = today.year + offset
        return date(year, 1, 1), date(year, MONTHS_PER_YEAR, calendar.monthrange(year, MONTHS_PER_YEAR)[1])
    raise ValueError(f"Unknown period unit: {unit!r}")  # pragma: no cover - PERIOD_PHRASES is the only caller


def _matched_month_name(duration: str) -> tuple[str, int] | None:
    """
    Return (name, month_number) for a recognized "in <month>" phrase in
    `duration` (see MONTH_NUMBERS), or None if none match.

    Requires the literal "in" right before the name, not a bare
    word-boundary match - "may"/"march"/"august" are also everyday
    words ("I may go"), and a bare match would confidently produce a
    wrong date instead of failing honestly.
    """
    lowered = duration.lower()
    for name, number in MONTH_NUMBERS.items():
        if re.search(r"\bin\s+" + re.escape(name) + r"\b", lowered):
            return name, number
    return None


def _month_name_range(month: int) -> tuple[date, date]:
    """
    The (start, end) date range for the nearest occurrence of `month`
    (1-12) that hasn't fully passed yet - this year if `month` is this
    month or later, otherwise next year. Said in August, "in March"
    means next March, not the one already gone by.
    """
    today = _now().date()
    year = today.year if month >= today.month else today.year + 1
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start, end


def _matched_weekday_name(duration: str) -> tuple[str, int, str | None] | None:
    """
    Return (weekday_name, isoweekday_number, prefix) for the first
    recognized weekday name in `duration` (see WEEKDAY_NUMBERS) -
    `prefix` is "next"/"this"/"last" if one precedes the name, else
    None for a bare name ("Monday" on its own). See _weekday_name_date()
    for how a bare name differs from an explicit prefix.
    """
    lowered = duration.lower()
    for name, number in WEEKDAY_NUMBERS.items():
        for prefix in WEEKDAY_PREFIXES:
            if re.search(r"\b" + prefix + r"\s+" + re.escape(name) + r"\b", lowered):
                return name, number, prefix
        if re.search(r"\b" + re.escape(name) + r"\b", lowered):
            return name, number, None
    return None


def _weekday_name_date(number: int, prefix: str | None) -> date:
    """
    The actual calendar date `number` (1=Monday..7=Sunday) + `prefix`
    refers to.

    A bare name (prefix is None) means the nearest occurrence, counting
    today itself if today already is that weekday - different from
    both "this" (the current week's occurrence, even if already past)
    and "next" (the following week's, skipping today's).
    """
    today = _now().date()
    if prefix is None:
        days_ahead = (number - today.isoweekday()) % DAYS_PER_WEEK
        return today + timedelta(days=days_ahead)
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=WEEKDAY_PREFIXES[prefix])
    return week_start + timedelta(days=number - 1)


# 4. Seasons


def _matched_season_name(duration: str) -> tuple[str, str | None] | None:
    """
    Return (season, prefix) for the first recognized season name in
    `duration` (see time_segments.NORTHERN_SEASON_MONTHS's keys, shared
    by SOUTHERN_SEASON_MONTHS, and SEASON_ALIASES for "fall") - `prefix`
    is "next"/"this"/"last" (WEEKDAY_PREFIXES, reused here for the same
    offset meaning - not a second identical table) if one precedes the
    name, else None for a bare name. `season` is always the canonical
    name ("autumn" for a matched "fall"). Recognition only - resolving
    it to actual dates needs a hemisphere, which this function has no
    opinion on (see _season_range()).
    """
    lowered = duration.lower()
    for name in list(NORTHERN_SEASON_MONTHS) + list(SEASON_ALIASES):
        canonical = SEASON_ALIASES.get(name, name)
        for prefix in WEEKDAY_PREFIXES:
            if re.search(r"\b" + prefix + r"\s+" + re.escape(name) + r"\b", lowered):
                return canonical, prefix
        if re.search(r"\b" + re.escape(name) + r"\b", lowered):
            return canonical, None
    return None


def _season_month_range(season: str, hemisphere: str) -> tuple[int, int]:
    """(start_month, end_month), both 1-12, for `season` in
    `hemisphere` ("northern"/"southern" - see NORTHERN_SEASON_MONTHS/
    SOUTHERN_SEASON_MONTHS). Raises ValueError for any other
    `hemisphere` value - callers are expected to validate it, same
    trust-the-shape approach _period_range() already takes for `unit`."""
    if hemisphere == "northern":
        return NORTHERN_SEASON_MONTHS[season]
    if hemisphere == "southern":
        return SOUTHERN_SEASON_MONTHS[season]
    raise ValueError(f"Unknown hemisphere: {hemisphere!r}")


def _season_occurrence(season: str, hemisphere: str, year: int) -> tuple[date, date]:
    """(start, end) for `season`'s occurrence anchored at `year` - the
    calendar year its start month falls in. `end` lands in `year + 1`
    for a season whose end month is earlier than its start month (e.g.
    Northern winter, Dec -> Feb) - same wrap-around DAY_SEGMENTS'
    "night" already needs, one calendar level up."""
    start_month, end_month = _season_month_range(season, hemisphere)
    start = date(year, start_month, 1)
    end_year = year + 1 if end_month < start_month else year
    end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
    return start, end


def _season_range(season: str, hemisphere: str, prefix: str | None) -> tuple[date, date]:
    """
    The (start, end) date range for `season` in `hemisphere`.

    An explicit `prefix` ("next"/"this"/"last") anchors the season to
    today's calendar year shifted by that offset (WEEKDAY_PREFIXES) -
    "this summer" is always the current year's summer, whether or not
    it has already passed, same as PERIOD_PHRASES' "this year".

    A bare name (`prefix` is None) instead means the nearest occurrence
    that hasn't fully ended yet, checking last year's anchor first (a
    wrapping season, e.g. Northern winter, can still be ongoing into
    the new year) - same "hasn't fully passed" reasoning
    _month_name_range() already uses for a bare month name.
    """
    today = _now().date()
    if prefix is not None:
        return _season_occurrence(season, hemisphere, today.year + WEEKDAY_PREFIXES[prefix])
    for candidate_year in (today.year - 1, today.year):
        start, end = _season_occurrence(season, hemisphere, candidate_year)
        if end >= today:
            return start, end
    return _season_occurrence(season, hemisphere, today.year + 1)


# 5. Named fractions & lengths


def _matched_named_fraction(duration: str) -> tuple[str, str, int] | None:
    """
    Return (segment_word, unit, value) for a recognized "quarter/half/
    three quarters (of a/an) hour/minute/day" phrase (see
    NAMED_FRACTION_RE), or None if none match. `value` is looked up in
    whichever of HOUR_SEGMENTS/MINUTE_SEGMENTS/DAY_FRACTIONS matches
    `unit` (see _FRACTION_TABLES above) - each table has its own scale.
    """
    match = NAMED_FRACTION_RE.search(duration)
    if not match:
        return None
    segment, unit = match.group(1).lower(), match.group(2).lower()
    return segment, unit, _FRACTION_TABLES[unit][segment]


def _named_fraction_end(unit: str, value: int) -> datetime:
    """
    The actual clock time `value` from now, for a recognized named
    fraction - `value` is already in the right scale for `unit`
    (minutes for hour, seconds for minute, hours for day). All three
    resolve to a clock time since a day or less always has a
    meaningful time-of-day.
    """
    now = _now()
    if unit == "hour":
        return now + timedelta(minutes=value)
    if unit == "minute":
        return now + timedelta(seconds=value)
    if unit == "day":
        return now + timedelta(hours=value)
    raise ValueError(f"Unknown fraction unit: {unit!r}")  # pragma: no cover - NAMED_FRACTION_RE is the only caller


def _matched_length(duration: str) -> tuple[int, str] | None:
    """Return (number, unit) for the first recognized "N minutes/hours/
    days/weeks/months/years/decades/centuries/millennia" phrase in
    `duration` (see time_segments.DURATION_LENGTH_RE), or None if none
    match. `unit` is always singular ("day", not "days") - including
    "century"/"millennium" for a matched "centuries"/"millennia",
    DURATION_LENGTH_RE's irregular plurals."""
    match = DURATION_LENGTH_RE.search(duration)
    if not match:
        return None
    unit = match.group(2).lower()
    if unit == "centuries":
        unit = "century"
    elif unit == "millennia":
        unit = "millennium"
    return int(match.group(1)), unit


def _length_end_date(number: int, unit: str) -> date | None:
    """
    The actual calendar date `number` `unit`s from today - "3 days"
    becomes a real end date the same way "next week" already does.

    None for minute/hour: there's no useful calendar date for a
    same-day span that short (see describe_duration()).

    Reuses _add_months() for month, year, decade, century, and
    millennium alike (a decade is 10 years, a century 100, a
    millennium 1000 - see YEARS_PER_DECADE/YEARS_PER_CENTURY/
    YEARS_PER_MILLENNIUM) - so every calendar-based length lands on
    the correct real date without a separate unit-equivalence table.
    """
    today = _now().date()
    if unit in ("minute", "hour"):
        return None
    if unit == "day":
        return today + timedelta(days=number)
    if unit == "week":
        return today + timedelta(weeks=number)
    if unit == "month":
        return _add_months(today, number)
    if unit == "year":
        return _add_months(today, number * MONTHS_PER_YEAR)
    if unit == "decade":
        return _add_months(today, number * YEARS_PER_DECADE * MONTHS_PER_YEAR)
    if unit == "century":
        return _add_months(today, number * YEARS_PER_CENTURY * MONTHS_PER_YEAR)
    if unit == "millennium":
        return _add_months(today, number * YEARS_PER_MILLENNIUM * MONTHS_PER_YEAR)
    return None  # pragma: no cover - DURATION_LENGTH_RE is the only caller


def _length_end_time(number: int, unit: str) -> datetime | None:
    """
    The actual clock date+time `number` `unit`s from now, for
    minute/hour lengths. A calendar date isn't the meaningful grounding
    for a span this short (see _length_end_date() for day/week/month/
    year, where it is).
    """
    now = _now()
    if unit == "minute":
        return now + timedelta(minutes=number)
    if unit == "hour":
        return now + timedelta(hours=number)
    return None


def _matched_period_phrase(duration: str) -> tuple[str, tuple[date, date]] | None:
    """Return (phrase, (start_date, end_date)) for the first known
    PERIOD_PHRASES entry found in `duration`, or None if none match."""
    lowered = duration.lower()
    for phrase, (unit, offset) in PERIOD_PHRASES.items():
        if _contains_phrase(lowered, phrase):
            return phrase, _period_range(unit, offset)
    return None


# 6. Public entry point


def extract_duration_phrase(text: str) -> str | None:
    """
    The raw, literal time-phrase found somewhere within `text` (e.g.
    "30 minutes", "this week", "before bed") - for when goal text and
    duration are typed together as one free-text sentence, e.g. "clean
    the apartment this weekend". None if nothing in `text` is
    recognized.

    Tries the same matchers duration_resolution.resolve_duration()
    does, in the same order, returning as soon as one hits - but
    doesn't call resolve_duration() itself, since that returns a
    resolved description ("evening (resolved: ...)"), not the plain
    phrase callers here want.
    """
    if not text:
        return None
    day_match = _matched_day_segment(text)
    if day_match is not None:
        return day_match[0]
    clock_match = CLOCK_12H_RE.search(text) or CLOCK_24H_RE.search(text)
    if clock_match is not None:
        return clock_match.group(0)
    period_match = _matched_period_phrase(text)
    if period_match is not None:
        return period_match[0]
    month_match = _matched_month_name(text)
    if month_match is not None:
        return f"in {month_match[0]}"
    season_match = _matched_season_name(text)
    if season_match is not None:
        season, prefix = season_match
        return f"{prefix} {season}" if prefix else season
    weekday_match = _matched_weekday_name(text)
    if weekday_match is not None:
        name, _, prefix = weekday_match
        return f"{prefix} {name}" if prefix else name
    deadline_match = _matched_deadline_phrase(text)
    if deadline_match is not None:
        return deadline_match
    fraction_match = _matched_named_fraction(text)
    if fraction_match is not None:
        segment, unit, _ = fraction_match
        return f"{segment} {unit}"
    length_match = DURATION_LENGTH_RE.search(text)
    if length_match is not None:
        return length_match.group(0)
    return None
