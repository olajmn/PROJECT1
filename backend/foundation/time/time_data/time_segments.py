"""
Time Segments
=============

The fixed rules recognized about "when"/"how long" - tables and
patterns only, no logic. See the sibling time_logic/ package for what
actually applies these to a piece of text. Raw time-unit arithmetic
lives in time_units.py instead - a different kind of fact, never
itself matched against typed text.

Contents
1. Calendar names
2. Named segments / fractions
3. Point-in-time recognition
4. Duration / quantity recognition
"""

import re

from backend.foundation.time.time_data.time_units import HOURS_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_MINUTE

# Calendar names

# 1-indexed to match datetime.isoweekday() (1=Monday..7=Sunday) and
# datetime.month (1-12), so a caller can index these directly.
WEEKDAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}
MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

# Named segments / fractions

# Named chunks of a minute, in seconds - called SEGMENTS rather than
# FRACTIONS because "minute" (the whole unit) is included alongside
# the actual fractions ("quarter"/"half"/"three quarters"). Matched via
# NAMED_FRACTION_RE below. Arbitrary counts ("45 minutes") are handled
# separately, by DURATION_LENGTH_RE.
MINUTE_SEGMENTS = {
    "quarter": 15,
    "half": 30,
    "three quarters": 45,
    "minute": SECONDS_PER_MINUTE,
}

# Same idea one level up: named chunks of an hour, in minutes. Values
# match MINUTE_SEGMENTS only because a minute and an hour both split
# into 60 of the unit below them, not because one reuses the other.
HOUR_SEGMENTS = {
    "quarter": 15,
    "half": 30,
    "three quarters": 45,
    "hour": MINUTES_PER_HOUR,
}

# The regular, mathematical quartering of a day, in hours - distinct
# from DAY_SEGMENTS below, which names real (irregular-length) periods
# like "morning"/"evening" rather than exact fractions.
DAY_FRACTIONS = {
    "quarter": HOURS_PER_DAY // 4,
    "half": HOURS_PER_DAY // 2,
    "three quarters": HOURS_PER_DAY * 3 // 4,
    "day": HOURS_PER_DAY,
}

# No WEEK_FRACTIONS: 7 doesn't divide evenly by 4. No YEAR_FRACTIONS
# either - MONTH_NAMES above already covers naming a specific part of
# a year, and nothing else depends on a year fraction existing.

# Point-in-time recognition

# Named day segments as local clock ranges, both hours in [0, 24).
# "night" wraps past midnight (23 -> 6) - handled specially in
# time_logic.resolve_duration(). English only (see CONVENTIONS.md) -
# a duration typed in another language still flows into the model
# prompt, so silent mixed-language recognition isn't worth the risk.
DAY_SEGMENTS = {
    "morning": (6, 12),
    "afternoon": (12, 17),
    "evening": (17, 23),
    "tonight": (17, 23),
    "night": (23, 6),
}

# Relative calendar periods -> (unit, offset). Stored as an offset
# rather than a fixed date range because e.g. "this week" means a
# different range every time depending on today's date -
# time_logic._period_range() resolves the actual dates at call time.
PERIOD_PHRASES = {
    "yesterday": ("day", -1),
    "today": ("day", 0),
    "tomorrow": ("day", 1),
    "last week": ("week", -1),
    "this week": ("week", 0),
    "next week": ("week", 1),
    "last month": ("month", -1),
    "this month": ("month", 0),
    "next month": ("month", 1),
    "last year": ("year", -1),
    "this year": ("year", 0),
    "next year": ("year", 1),
}

# Reverse lookups, derived from MONTH_NAMES/WEEKDAY_NAMES above rather
# than typed out by hand, so a name and its number can never drift
# apart. Lowercased to match how every phrase here is matched.
MONTH_NUMBERS = {name.lower(): number for number, name in MONTH_NAMES.items()}
WEEKDAY_NUMBERS = {name.lower(): number for number, name in WEEKDAY_NAMES.items()}

# "next Monday" / "this Monday" / "last Monday" -> week offset. A bare
# weekday name with no prefix is NOT a fourth entry here with offset
# 0 - it means the nearest occurrence, not "this week's", so it's
# resolved separately (see time_logic._weekday_name_date()).
WEEKDAY_PREFIXES = {
    "next": 1,
    "this": 0,
    "last": -1,
}

# Exact clock times, 12-hour and 24-hour notation. Two separate
# regexes since a bare 24h "14:30" is never followed by am/pm/o'clock.
# A bare "o'clock" with no am/pm ("1 o'clock") is genuinely ambiguous -
# time_logic._matched_clock_time() resolves it to PM as a deliberate,
# documented convention, not a guess.
CLOCK_12H_RE = re.compile(
    r"\b(\d{1,2})(?::([0-5]\d))?\s*(o'clock|am|pm)\b", re.IGNORECASE
)
CLOCK_24H_RE = re.compile(r"\b([01]\d|2[0-3]):([0-5]\d)\b")

# A deadline tied to a personal routine event ("before bed"), not a
# clock time - there's no real clock time to resolve this to (we don't
# track when the user goes to bed), so it's recognized only so
# describe_duration() can say what it honestly is. A regex, not a
# fixed phrase list, to tolerate "before I go/got/going to bed" as
# well as "before bed" alone. English only, same reasoning as
# DAY_SEGMENTS above.
DEADLINE_RE = re.compile(
    r"before\s+(?:i\s+)?(?:\w+\s+to\s+)?(bed(?:time)?|sleep)",
    re.IGNORECASE,
)

# Duration / quantity recognition

# A plain "N minutes/hours/days/weeks/months/years" phrase - a counted
# span, as opposed to a day segment or named period above.
DURATION_LENGTH_RE = re.compile(
    r"\b(\d+)\s*(minute|hour|day|week|month|year)s?\b", re.IGNORECASE
)

# A named fraction ("half an hour", "quarter of a day") - the phrase-
# recognition counterpart to DURATION_LENGTH_RE above. Only recognizes
# the phrase; time_logic._matched_named_fraction() looks the matched
# value up in whichever of HOUR_SEGMENTS/MINUTE_SEGMENTS/DAY_FRACTIONS
# matches. No "year" - year fractions aren't recognized this way.
NAMED_FRACTION_RE = re.compile(
    r"\b(quarter|half|three quarters)\s+(?:of\s+)?(?:an?\s+)?(hour|minute|day)\b",
    re.IGNORECASE,
)
