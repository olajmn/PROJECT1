"""
Understanding "when" a plan should span - free text like "evening",
"30 minutes", or "this month" - grounded in a real clock window or
calendar date range where the code can actually know one, honest about
what it can't.

The recognized phrases/patterns themselves (DAY_SEGMENTS, PERIOD_PHRASES,
etc.) live in backend/timesegments.py, not here - this file is the
logic that resolves and describes them. Split apart 2026-08-21 so the
data (what's recognized) and the logic (what happens with it) can each
be read on their own.

Split out of goal_to_plan.py (2026-08-21) so this concept has its own
file, matching the product model in docs/07-features.md ("Architecture
framing: Program / Rooms / Sitemap") - Timeperiod is its own room,
not a few fields buried inside plan-generation code.

Future hook (not built yet, see docs/12-decisions.md, 2026-08-21 and
docs/08-technical-architecture.md § Memory & Data Architecture):
this module is where a real year -> month -> week -> day -> hour ->
minute hierarchy would eventually live, if/when flat duration strings
stop being enough - e.g. a `resolve_hierarchy()` alongside today's
`_resolve_duration()`, walking a structured scale instead of matching
free text. Deliberately not started now - only day/week/month/year
phrase recognition lives here today, not a real walkable hierarchy.
"""

import calendar
import re
from datetime import date, datetime, timedelta

from backend.timesegments import (
    CLOCK_12H_RE,
    CLOCK_24H_RE,
    DAY_FRACTIONS,
    DAY_SEGMENTS,
    DAYS_PER_WEEK,
    DEADLINE_RE,
    DURATION_LENGTH_RE,
    HOUR_SEGMENTS,
    MINUTE_SEGMENTS,
    MONTH_NUMBERS,
    MONTHS_PER_YEAR,
    NAMED_FRACTION_RE,
    PERIOD_PHRASES,
    WEEKDAY_NUMBERS,
    WEEKDAY_PREFIXES,
)

# Which of the three section-3 tables a NAMED_FRACTION_RE match's unit
# word belongs to - the single place that dispatch is decided, so
# _matched_named_fraction() doesn't need an if/elif chain of its own.
# No "year" entry (YEAR_FRACTIONS removed 2026-08-21, see
# docs/12-decisions.md).
_FRACTION_TABLES = {
    "hour": HOUR_SEGMENTS,
    "minute": MINUTE_SEGMENTS,
    "day": DAY_FRACTIONS,
}


def _matched_day_segment(duration: str) -> tuple[str, tuple[int, int]] | None:
    """Return (word, (start_hour, end_hour)) for the first known day
    segment found in `duration`, or None if none match."""
    lowered = duration.lower()
    for word, hours in DAY_SEGMENTS.items():
        if word in lowered:
            return word, hours
    return None


def _matched_day_offset(duration: str) -> int:
    """
    0 (today) by default, or the +/-N day offset if `duration` also
    names yesterday/today/tomorrow (see timesegments.PERIOD_PHRASES'
    "day" entries) - so a day segment can combine with it correctly.

    Found via real use, 2026-08-21: "tomorrow evening" was resolving
    against *today's* date ("resolved: today 2026-08-21, 17:00-23:00"),
    silently ignoring the "tomorrow" the user actually typed. Day
    segments (DAY_SEGMENTS) only ever knew about clock hours, never
    about which day those hours belonged to - always assumed today.
    """
    lowered = duration.lower()
    for phrase, (unit, offset) in PERIOD_PHRASES.items():
        if unit == "day" and phrase in lowered:
            return offset
    return 0


def _matched_clock_time(duration: str) -> tuple[int, int] | None:
    """
    Return (hour, minute) in 24h form for a recognized literal clock
    time in `duration` - 12-hour ("1 o'clock", "3pm", "11:30am") or
    24-hour ("14:30", "00:00") (see timesegments.CLOCK_12H_RE/
    CLOCK_24H_RE). None if none match.

    A bare "o'clock" with no am/pm ("1 o'clock") resolves to PM - see
    CLOCK_12H_RE's comment in timesegments.py for why that's a named
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
    event deadline (see timesegments.DEADLINE_RE), or None if none match."""
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
    today's real date - see timesegments.PERIOD_PHRASES. "day" returns
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
    `duration` (see timesegments.MONTH_NUMBERS), or None if none match.

    Requires the literal "in" right before the name - NOT a bare
    word-boundary match on the month name alone. Found via real testing
    2026-08-21: "I may go" was silently "resolving" to next May, and
    "this may take a while" to the same - "may" (the month) and "may"
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
    timesegments.WEEKDAY_NUMBERS) - `prefix` is "next"/"this"/"last" if
    one of those (timesegments.WEEKDAY_PREFIXES) directly precedes the
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
    timesegments.NAMED_FRACTION_RE), or None if none match. `value` is
    looked up in whichever of HOUR_SEGMENTS/MINUTE_SEGMENTS/
    DAY_FRACTIONS matches `unit` (see _FRACTION_TABLES above) -
    minutes/seconds/hours respectively, matching each table's own scale
    (see timesegments.py).
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
    timesegments.DURATION_LENGTH_RE), or None if none match. `unit` is
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


def _format_date_range(start_date: date, end_date: date) -> str:
    """A single date on its own ("2026-08-22") when start and end are
    the same day (yesterday/today/tomorrow), "X to Y" otherwise."""
    if start_date == end_date:
        return start_date.isoformat()
    return f"{start_date.isoformat()} to {end_date.isoformat()}"


def _matched_period_phrase(duration: str) -> tuple[str, tuple[date, date]] | None:
    """Return (phrase, (start_date, end_date)) for the first known
    PERIOD_PHRASES entry found in `duration`, or None if none match."""
    lowered = duration.lower()
    for phrase, (unit, offset) in PERIOD_PHRASES.items():
        if phrase in lowered:
            return phrase, _period_range(unit, offset)
    return None


def _resolve_duration(duration: str | None) -> str | None:
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
