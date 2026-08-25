"""
Phrase-matching primitives: recognize a known time phrase somewhere in
free text and turn it into hard values (hours, dates, offsets), using
the pattern tables in the sibling time_data/ package's time_segments.py. Nothing here decides
what to DO with a match (see duration_resolution.py) or how to describe it to the
user (also duration_resolution.py) - just "is this phrase here, and what does it
concretely mean".

extract_duration_phrase() is the one function in this file meant to be
called from outside the package: the raw phrase text itself (not a
resolved description), for pulling a duration out of a longer
free-text sentence typed together with the goal - see duration_resolution.py's
resolve_duration() for the resolved-description counterpart, and
docs/05-decisions.md, 2026-08-23, for why the two return different
things.
"""

import calendar
import re
from datetime import date, datetime, timedelta

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
    PERIOD_PHRASES,
    WEEKDAY_NUMBERS,
    WEEKDAY_PREFIXES,
)
from backend.foundation.time.time_data.time_units import DAYS_PER_WEEK, MONTHS_PER_YEAR

# Which of the three section-2 tables a NAMED_FRACTION_RE match's unit
# word belongs to - the single place that dispatch is decided, so
# _matched_named_fraction() doesn't need an if/elif chain of its own.
# No "year" entry (YEAR_FRACTIONS removed 2026-08-21, see
# docs/05-decisions.md).
_FRACTION_TABLES = {
    "hour": HOUR_SEGMENTS,
    "minute": MINUTE_SEGMENTS,
    "day": DAY_FRACTIONS,
}


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Whether `phrase` (already lowercase) appears in `text` as whole
    word(s), not just as a substring - `"this week" in "this weekend"`
    is True with a plain substring check but wrong, the same shape of
    bug `_matched_month_name()` already found and fixed for month names
    colliding with everyday words ("I may go" - see its docstring).
    Only mattered lightly before 2026-08-23 (duration used to live in
    its own short, dedicated field, where an accidental collision was
    unlikely) - became a real risk once goal text and duration are
    typed together as one free-text sentence, where "weekend"/
    "midnight"/etc are much more likely to actually appear.
    """
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


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
    names yesterday/today/tomorrow (see time_segments.PERIOD_PHRASES'
    "day" entries) - so a day segment can combine with it correctly.

    Without this (2026-08-21): "tomorrow evening" would resolve against
    *today's* date ("resolved: today 2026-08-21, 17:00-23:00"), silently
    ignoring the "tomorrow" actually typed. Day segments (DAY_SEGMENTS)
    only ever knew about clock hours, never about which day those hours
    belonged to - always assumed today.
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
    24-hour ("14:30", "00:00") (see time_segments.CLOCK_12H_RE/
    CLOCK_24H_RE). None if none match.

    A bare "o'clock" with no am/pm ("1 o'clock") resolves to PM - see
    CLOCK_12H_RE's comment in time_segments.py for why that's a named
    convention, not a guess.
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
    target_date = datetime.now().date() + timedelta(days=_matched_day_offset(duration))
    return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))


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
    today = datetime.now().date()
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
    `duration` (see time_segments.MONTH_NUMBERS), or None if none match.

    Requires the literal "in" right before the name - NOT a bare
    word-boundary match on the month name alone (2026-08-21): without
    it, "I may go" would silently "resolve" to next May, and "this may
    take a while" to the same - "may" (the month) and "may"
    (the everyday modal verb) are the same word, and "march"/"august"
    have the identical problem (verb / adjective). A bare match doesn't
    just fail honestly here, the way an unrecognized phrase normally
    does - it confidently states a wrong date, which is worse. Requiring
    "in" first (mirrors DEADLINE_RE requiring "before") is the same
    trade DEADLINE_RE already makes: narrower matching, but nothing it
    does match is a false positive.
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
    means *next* March, not the one already gone by - the same
    real-world meaning a person means by it, not an arbitrary pick
    between the two.
    """
    today = datetime.now().date()
    year = today.year if month >= today.month else today.year + 1
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start, end


def _matched_weekday_name(duration: str) -> tuple[str, int, str | None] | None:
    """
    Return (weekday_name, isoweekday_number, prefix) for the first
    recognized weekday name found in `duration` (see
    time_segments.WEEKDAY_NUMBERS) - `prefix` is "next"/"this"/"last" if
    one of those (time_segments.WEEKDAY_PREFIXES) directly precedes the
    name, else None for a bare name ("Monday" on its own). See
    _weekday_name_date() for why a bare name resolves differently from
    an explicit prefix rather than defaulting to one of them.
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
    The actual calendar date `number` (1=Monday..7=Sunday, matching
    WEEKDAY_NAMES) + `prefix` refers to.

    A bare name (prefix is None) means the *nearest* occurrence,
    counting today itself as a match if today already is that weekday -
    genuinely different from both "this" (the current calendar week's
    occurrence specifically, even if it's already gone by) and "next"
    (the following week's, skipping an occurrence today would count
    as), not a shorthand for either.
    """
    today = datetime.now().date()
    if prefix is None:
        days_ahead = (number - today.isoweekday()) % DAYS_PER_WEEK
        return today + timedelta(days=days_ahead)
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=WEEKDAY_PREFIXES[prefix])
    return week_start + timedelta(days=number - 1)


def _matched_named_fraction(duration: str) -> tuple[str, str, int] | None:
    """
    Return (segment_word, unit, value) for a recognized "quarter/half/
    three quarters (of a/an) hour/minute/day" phrase (see
    time_segments.NAMED_FRACTION_RE), or None if none match. `value` is
    looked up in whichever of HOUR_SEGMENTS/MINUTE_SEGMENTS/
    DAY_FRACTIONS matches `unit` (see _FRACTION_TABLES above) -
    minutes/seconds/hours respectively, matching each table's own scale
    (see time_segments.py).
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
    (minutes for hour, seconds for minute, hours for day; see
    _matched_named_fraction()). All three resolve to a clock *time*
    (now + minutes/seconds/hours) - a day or less always has a
    meaningful time-of-day.
    """
    now = datetime.now()
    if unit == "hour":
        return now + timedelta(minutes=value)
    if unit == "minute":
        return now + timedelta(seconds=value)
    if unit == "day":
        return now + timedelta(hours=value)
    raise ValueError(f"Unknown fraction unit: {unit!r}")  # pragma: no cover - NAMED_FRACTION_RE is the only caller


def _matched_length(duration: str) -> tuple[int, str] | None:
    """Return (number, unit) for the first recognized "N minutes/hours/
    days/weeks/months/years" phrase in `duration` (see
    time_segments.DURATION_LENGTH_RE), or None if none match. `unit` is
    always singular ("day", not "days")."""
    match = DURATION_LENGTH_RE.search(duration)
    if not match:
        return None
    return int(match.group(1)), match.group(2).lower()


def _length_end_date(number: int, unit: str) -> date | None:
    """
    The actual calendar date `number` `unit`s from today - "3 days"
    becomes a real end date the same way "next week" already does,
    instead of stopping at "recognized as a length, not grounded".

    None for minute/hour: there's no useful *calendar date* to compute
    for a same-day span that short (see describe_duration(), which
    reports those as recognized-but-ungrounded, same as before).

    Reuses _add_months() for both month and year (year = 12 months) -
    this is *why* the code doesn't need to separately know "12 months
    is 1 year": both go through the same date arithmetic and land on
    the same real date, rather than needing a unit-equivalence table.
    """
    today = datetime.now().date()
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
    return None  # pragma: no cover - DURATION_LENGTH_RE is the only caller


def _length_end_time(number: int, unit: str) -> datetime | None:
    """
    The actual clock date+time `number` `unit`s from *right now*, for
    minute/hour lengths - "2 hours" becomes an actual "today HH:MM"
    instead of stopping at "recognized as a length, not grounded in a
    clock time". A calendar date isn't the meaningful grounding for a
    span this short (see _length_end_date() for day/week/month/year,
    where a date is what matters and a specific minute wouldn't add
    anything); this is that same idea one level finer.
    """
    now = datetime.now()
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


def extract_duration_phrase(text: str) -> str | None:
    """
    The raw, literal time-phrase found somewhere within `text` (e.g.
    "30 minutes", "this week", "before bed") - for when goal text and
    duration are typed together as one free-text sentence (2026-08-23),
    e.g. "clean the apartment this weekend", rather than two separate
    form fields. None if nothing in `text` is recognized at all - see
    resolve.describe_duration()'s "not parsed/verified by code"
    fallback for the same honesty applied to a whole dedicated duration
    field.

    Tries the same matchers resolve.resolve_duration() does, in the
    same broadest-signal-first order, returning as soon as one hits.
    Doesn't just call resolve_duration() and reuse its output, though:
    that returns a RESOLVED description ("evening (resolved: ...)"),
    not the plain phrase on its own - callers here want something short
    enough to still read naturally as `duration` on its own (e.g. in
    the Timeperiod row), not the goal's whole sentence repeated back
    with a resolution note stapled on.
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
