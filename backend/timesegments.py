"""
Recognized time-phrase DATA only - no logic, no functions that resolve
or interpret any of it. Split out of timeperiod.py (2026-08-21) purely
for overview: everything the code currently knows how to recognize
about "when" lives in this one file, scannable at a glance, without
wading through the resolution logic that uses it (that logic - actual
date/time arithmetic, matching, describing - stays in timeperiod.py,
which imports these tables from here).

Nothing here does anything by itself - these are just tables and
patterns; see backend/timeperiod.py for what turns them into an actual
answer.
"""

import re

# =============================================================================
# SECTION 1 — BASIC TIME-UNIT FACTS
#
# Not phrase recognition like sections 4-5 below - just the real-world
# constants everything else in this file (and timeperiod.py's
# arithmetic) is actually built from, written down explicitly in one
# place instead of left as bare numbers (60, 24, 7, 12) scattered
# through the code with no name attached. Sections 2-3 aren't
# recognition either, for that matter - see their own banners: they're
# named/derived *data*, only sections 4-5 actually match against typed
# text.
# =============================================================================

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MONTHS_PER_YEAR = 12

# Derived, not a separate fact of its own - always exactly
# MINUTES_PER_HOUR * HOURS_PER_DAY. Computed from those two rather than
# hardcoded as 1440 so it can never drift out of sync with them.
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY

# Months are 28-31 days and years are 365/366 days, so neither "days
# per month" nor "weeks per year" has a clean, exact whole-number
# answer the way days-per-week (always 7) or months-per-year (always
# 12) do. That doesn't mean there's only one honest answer, though -
# there are two different, both-real facts here, not a "right" one and
# a "wrong" one:
#
#   - the PRECISE mathematical average (below, computed from 365.25 to
#     account for leap years) - what you'd actually want for a
#     calculation that needs to be correct over many years.
#   - the CONVENTIONAL, commonly-said number (WEEKS_PER_MONTH = 4,
#     WEEKS_PER_YEAR = 52) - not an attempt at precision, but genuinely
#     what people mean when they say "four weeks" or "52 weeks" out
#     loud. Rounding 4.35 to "4" isn't an error here the way rounding a
#     calculation would be - it's a real, separate convention, not a
#     worse version of the average.
#
# For a *specific* month, the exact day count already exists elsewhere
# too - timeperiod.py uses calendar.monthrange(year, month) when it
# actually needs to know how many days September has, say (see
# MONTH_DAYS below for a non-leap-year reference table of the same
# fact). The averages here are for estimation across an unspecified
# span, never a substitute for an exact lookup once a real month/year
# is known.
WEEKS_PER_MONTH = 4
WEEKS_PER_YEAR = 52

AVERAGE_DAYS_PER_MONTH = 365.25 / MONTHS_PER_YEAR  # ~30.44
AVERAGE_WEEKS_PER_MONTH = AVERAGE_DAYS_PER_MONTH / DAYS_PER_WEEK  # ~4.35
AVERAGE_WEEKS_PER_YEAR = 365.25 / DAYS_PER_WEEK  # ~52.18

# The actual day count for each named month - 1-indexed to match
# MONTH_NAMES/datetime.month. February is written as 28 (the common
# case, not a leap year) - the one month where "how many days" doesn't
# have a single year-independent answer; calendar.monthrange(year, 2)
# is the exact answer for a specific year (see timeperiod.py), this is
# the everyday reference value.
MONTH_DAYS = {
    1: 31, 2: 28, 3: 31, 4: 30,
    5: 31, 6: 30, 7: 31, 8: 31,
    9: 30, 10: 31, 11: 30, 12: 31,
}

# =============================================================================
# SECTION 2 — CALENDAR NAMES
#
# Its own section, not folded into section 3 below - these two tables
# don't name a *fraction* of a unit the way everything in section 3
# does, they name the unit's own individual slots (each weekday, each
# month). A genuinely different kind of table, not a special case of
# the same one.
# =============================================================================

# Literal calendar names, 1-indexed to match Python's own
# datetime.isoweekday() (1=Monday..7=Sunday) / datetime.month (1-12) -
# so a future caller can do WEEKDAY_NAMES[some_date.isoweekday()] or
# MONTH_NAMES[some_date.month] directly, without an off-by-one
# translation.
WEEKDAY_NAMES = {
    1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
    5: "Friday", 6: "Saturday", 7: "Sunday",
}
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# =============================================================================
# SECTION 3 — NAMED SEGMENTS / FRACTIONS
#
# The *regular*, mathematical kind of named chunk - "half" is always
# exactly half, no matter which unit (HOUR_SEGMENTS/MINUTE_SEGMENTS/
# DAY_FRACTIONS all work the same way). DAY_SEGMENTS used to live here
# too, but moved to section 4 (Point-in-time recognition) - it's the
# *irregular* kind (real, named periods with their own meaning, like
# PERIOD_PHRASES), not a fraction of anything, and it's matched
# directly the same self-contained way PERIOD_PHRASES is, unlike every
# table still in this section.
#
# Ordered smallest unit to largest (minute -> hour -> day), same
# direction time itself accumulates in - not alphabetical, not by when
# each table was added. No week or year entry: see the "No
# WEEK_FRACTIONS"/"No YEAR_FRACTIONS" note below.
# =============================================================================

# Named segments of a minute, in seconds - "a quarter" / "half a
# minute" / "three quarters of a minute" / a full "minute" are things
# people actually say; recognized via NAMED_FRACTION_RE (section 5
# below), which looks values up in this table. Called SEGMENTS, not
# FRACTIONS: "quarter" isn't really "1/4" to whoever's typing it, it's
# a named chunk of the minute, same idea as DAY_SEGMENTS (section 4
# below) being named chunks of the day - and "fractions" stopped
# fitting the moment "minute" (the whole thing, not a fraction of
# itself) was added anyway. Arbitrary counts ("45 minutes") are a
# separate, more general case - see DURATION_LENGTH_RE below.
MINUTE_SEGMENTS = {
    "quarter": 15,
    "half": 30,
    "three quarters": 45,
    "minute": SECONDS_PER_MINUTE,
}

# Same idea, one level up: named segments of an hour, in minutes -
# "a quarter of an hour" / "half an hour" / "three quarters of an
# hour" / a full "hour" are things people actually say, same as
# MINUTE_SEGMENTS above, just with "an hour" instead of "a minute"
# (English's a/an split by vowel sound, not by which unit it is). The
# numbers happen to be identical to MINUTE_SEGMENTS (15/30/45/60) only
# because both a minute and an hour split into 60 of the unit below
# them - not because one is secretly reused as the other.
HOUR_SEGMENTS = {
    "quarter": 15,
    "half": 30,
    "three quarters": 45,
    "hour": MINUTES_PER_HOUR,
}

# Unlike DAY_SEGMENTS (section 4 below - irregular, named real periods,
# morning and afternoon aren't the same length), this is the *regular*
# mathematical quartering of a day, in hours - "half a day" = 12 hours,
# always, the same way "half an hour" always means 30 minutes
# (HOUR_SEGMENTS). Both are real, different things a day can mean, so
# both get their own table rather than picking one.
DAY_FRACTIONS = {
    "quarter": HOURS_PER_DAY // 4,
    "half": HOURS_PER_DAY // 2,
    "three quarters": HOURS_PER_DAY * 3 // 4,
    "day": HOURS_PER_DAY,
}

# No WEEK_FRACTIONS: 7 doesn't divide evenly by 4 (a "quarter week"
# would be 1.75 days) - not a clean, useful value the way DAY_FRACTIONS
# is, so left out rather than silently rounding to something that
# isn't actually what a quarter of a week is. WEEKDAY_NAMES (section 2
# above) covers the "named segments of a week" role instead
# (Monday..Sunday).
#
# No YEAR_FRACTIONS either (removed 2026-08-21, see
# docs/12-decisions.md) - not because a year can't be quartered
# cleanly (it can, into months, the same way DAY_FRACTIONS quarters a
# day into hours), but because it wasn't judged worth keeping: nothing
# else in this file depends on it, and MONTH_NAMES (section 2 above)
# already covers naming a specific part of a year.

# =============================================================================
# SECTION 4 — POINT-IN-TIME RECOGNITION
#
# What actually gets matched against the raw duration text typed in,
# for phrases that name a specific point in the calendar/clock - day
# segments (DAY_SEGMENTS), whole periods (PERIOD_PHRASES), calendar
# names used the other way around (MONTH_NUMBERS/WEEKDAY_NUMBERS/
# WEEKDAY_PREFIXES), literal clock times (CLOCK_12H_RE/CLOCK_24H_RE),
# and routine-event deadlines (DEADLINE_RE) - all answer "WHEN".
# Sections 1-3 above are just the underlying facts and named chunks;
# this is where free text starts turning into one of them. See section
# 5 below for the other kind of phrase recognition - "HOW LONG", not
# "WHEN".
# =============================================================================

# Recognized day segments: word -> (start_hour, end_hour) in 24h local
# time, both in [0, 24). "night" wraps past midnight (23 -> 6), handled
# specially in timeperiod.resolve_duration(). This is the code
# actually *knowing* what "evening" means (a real clock window) instead
# of handing the raw word to the model and hoping it guesses sensibly -
# see docs/11-experiments.md, 2026-08-19. Moved to this section
# 2026-08-21 - matched directly by its own key, the same self-contained
# way PERIOD_PHRASES just below is, not via a value table + separate
# matching regex the way section 3's segments/fractions are.
#
# English only (see CONVENTIONS.md) - this used to also recognize the
# Norwegian words for each segment ("morgen"/"formiddag" - morning,
# "ettermiddag" - afternoon, "kveld" - evening, "natt" - night).
# Dropped 2026-08-21 for the same reason goals are written in English
# (docs/12-decisions.md, 2026-08-19): a duration typed in Norwegian
# still flows into the prompt sent to the model, and mixed-language
# input is exactly the failure mode already found there. Anyone typing
# a day segment in Norwegian now gets the honest "not parsed/verified
# by code" fallback (see timeperiod.describe_duration()) instead of
# silent recognition.
DAY_SEGMENTS = {
    "morning": (6, 12),
    "afternoon": (12, 17),
    "evening": (17, 23),
    "tonight": (17, 23),
    "night": (23, 6),
}

# Same idea as DAY_SEGMENTS above, one level up: recognized whole-period
# phrases -> (unit, offset). Unlike DAY_SEGMENTS these can't be a fixed
# (start, end) tuple - "this week" means a different date range every
# time depending on today's date - so timeperiod._period_range()
# resolves each at call time instead of storing a fixed value here.
# Added 2026-08-21 alongside week/month/year so the model has the same
# real grounding for "by this evening" (a DAY_SEGMENTS phrase) and
# "this month" (a PERIOD_PHRASES one): both become an actual date/time
# range instead of a bare word. Deliberately still just a recognition
# table, not the folder-per-time-period hierarchy from
# docs/08-technical-architecture.md - see timeperiod.py's docstring.
#
# "day" as a unit (added 2026-08-21) is the same mechanism one level
# down from week/month/year: "tomorrow" is today's date + 1, exactly
# the same offset arithmetic as "next week" being this week + 1 - just
# a single day instead of a 7-day range, so timeperiod._period_range()
# returns (that day, that day) rather than (start, end).
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

# Reverse lookups (name -> number), derived directly from MONTH_NAMES/
# WEEKDAY_NAMES above (section 2) rather than typed out again by hand -
# a name and its number can never quietly drift apart, since one is
# computed from the other every time the module loads. Lowercased
# because every phrase this gets matched against is lowercased first,
# same as every other lookup in this file (e.g. DAY_SEGMENTS).
#
# This is what actually turns MONTH_NAMES/WEEKDAY_NAMES into phrase
# recognition rather than just a display lookup: those two tables on
# their own only answer "what's month number 3 called?" - matching
# typed text ("in March") needs the question asked the other way
# around, which is what these two dicts are for.
MONTH_NUMBERS = {name.lower(): number for number, name in MONTH_NAMES.items()}
WEEKDAY_NUMBERS = {name.lower(): number for number, name in WEEKDAY_NAMES.items()}

# Recognized relative-weekday prefixes -> week offset, same shape as
# PERIOD_PHRASES' (unit, offset) idea, just for a single day-of-week
# instead of a whole unit: "next Monday" means Monday of *next* week,
# "this Monday" means Monday of the *current* week (even if that date
# has already gone by), "last Monday" means Monday of *last* week.
#
# A bare weekday name with no prefix ("Monday", no "next"/"this"/
# "last") is deliberately not a fourth entry here with offset 0 - it
# doesn't mean the same thing as "this Monday". See
# timeperiod._weekday_name_date() for why a bare name gets its own,
# different resolution (the *nearest* occurrence, counting today).
WEEKDAY_PREFIXES = {
    "next": 1,
    "this": 0,
    "last": -1,
}

# A literal clock time - the specific-moment counterpart to
# DAY_SEGMENTS' clock *window* ("evening" = 17:00-23:00): "1 o'clock",
# "3pm", "11:30am" is one person actually names an exact point in the
# day, not a stretch of it. Two separate regexes, not one combined -
# 12h and 24h notation don't share a suffix the way DURATION_LENGTH_RE's
# units do, and a bare 24h "14:30" is never followed by am/pm/o'clock.
#
# A bare "o'clock" with no am/pm ("1 o'clock") is genuinely ambiguous -
# the text alone can't say whether that's 01:00 or 13:00. Rather than
# leave it unrecognized, timeperiod._matched_clock_time() resolves it
# to PM - a deliberate, named CONVENTION (not a fact the code actually
# knows), same trade WEEKS_PER_MONTH=4 already makes elsewhere in this
# file: a fixed, documented default beats silently guessing differently
# each time, or refusing to answer at all.
CLOCK_12H_RE = re.compile(
    r"\b(\d{1,2})(?::([0-5]\d))?\s*(o'clock|am|pm)\b", re.IGNORECASE
)

# Strict 24-hour "HH:MM", including midnight ("00:00") - HH must be
# 00-23 and MM 00-59. Checked in timeperiod.py only after CLOCK_12H_RE
# has already had a chance to match, so a 12-hour time like "11:30am"
# is never mistaken for a bare 24-hour one - the trailing "am" doesn't
# leave a word boundary for this regex to match on anyway (see
# timeperiod._matched_clock_time()).
CLOCK_24H_RE = re.compile(r"\b([01]\d|2[0-3]):([0-5]\d)\b")

# A deadline tied to a personal routine event, not a clock time - found
# via real test usage 2026-08-19 ("any time before i got to bed", see
# docs/11-experiments.md). Deliberately NOT given the same treatment as
# DAY_SEGMENTS: there's no real, known clock time to compute (we don't
# track when the user actually goes to bed), so resolving this to a
# fake hour would be inventing grounding that doesn't exist. Recognized
# only so describe_duration() can say what it honestly is - a same-day
# deadline with an unknown clock time - instead of lumping it in with
# genuinely unexamined free text.
#
# A regex, not a fixed phrase list: the first real test hit "before i
# got to bed" - a fixed list of exact phrases missed that variation
# ("got to" vs "go to"/"bed" alone). \w* around the verb tolerates
# go/going/got/getting; "to" and "i" are optional so "before bed" alone
# still matches too.
#
# English only (see CONVENTIONS.md) - this used to also match the
# Norwegian phrasing ("before I go to bed" / "before I lie down",
# literally "før jeg legger meg" / "innen jeg legger meg"), dropped
# 2026-08-21 for the same reason as DAY_SEGMENTS above.
DEADLINE_RE = re.compile(
    r"before\s+(?:i\s+)?(?:\w+\s+to\s+)?(bed(?:time)?|sleep)",
    re.IGNORECASE,
)

# =============================================================================
# SECTION 5 — DURATION / QUANTITY RECOGNITION
#
# The other kind of phrase recognition - not "WHEN" (section 4 above),
# but "HOW LONG": a counted span ("2 hours") or a named fraction
# ("half an hour") of time from now, rather than a fixed point on the
# calendar.
# =============================================================================

# A plain "N minutes/hours/days/weeks/months/years" phrase - the other
# case the code can actually understand (a real, countable span),
# rather than a day segment or named period. week/month/year added
# 2026-08-21 alongside PERIOD_PHRASES - until then this only recognized
# minute/hour/day, so "12 months" or "2 weeks" fell all the way through
# to "not parsed/verified by code", not even as far as "recognized as a
# length". timeperiod._length_end_date() turns (number, unit) into an
# actual end date - minute/hour have no useful calendar date to compute
# (see that function), day/week/month/year do.
DURATION_LENGTH_RE = re.compile(
    r"\b(\d+)\s*(minute|hour|day|week|month|year)s?\b", re.IGNORECASE
)

# A named fraction of an hour/minute/day - "half an hour", "quarter of
# a day", "three quarters of an hour" - the phrase-recognition
# counterpart to DURATION_LENGTH_RE just above: that one is a *counted*
# amount ("2 hours"), this one is a *named* one, reusing the actual
# values already sitting in HOUR_SEGMENTS/MINUTE_SEGMENTS/DAY_FRACTIONS
# (section 3 above) rather than a fourth copy of them. This regex only
# recognizes the phrase - it doesn't carry a value itself;
# timeperiod._matched_named_fraction() looks the matched (segment,
# unit) pair up in whichever of those three tables the matched unit
# belongs to. No "year" here (YEAR_FRACTIONS removed 2026-08-21, see
# docs/12-decisions.md) - "half a year"/"quarter of a year" are no
# longer recognized this way.
#
# One combined regex across all three units (same style as
# DURATION_LENGTH_RE's unit alternation), not three near-identical ones -
# "hour"/"minute"/"day" is the only thing that differs between them.
# Deliberately only matches "quarter"/"half"/"three quarters", not a
# bare unit name alone ("an hour") - that's already DURATION_LENGTH_RE's
# job once phrased as "1 hour", so there's nothing new to recognize
# there.
NAMED_FRACTION_RE = re.compile(
    r"\b(quarter|half|three quarters)\s+(?:of\s+)?(?:an?\s+)?(hour|minute|day)\b",
    re.IGNORECASE,
)
