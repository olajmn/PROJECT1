"""
The real-world time-unit constants everything else in this faculty
(time_segments.py's tables, time_logic/'s arithmetic) is actually
built from - written down explicitly in one place instead of left as
bare numbers (60, 24, 7, 12) scattered through the code with no name
attached. No logic, no functions - just facts.

Split out of time_segments.py (2026-08-25) once that file grew a
second, genuinely different kind of table alongside its
phrase-recognition tables: these constants aren't matched against
typed text the way DAY_SEGMENTS/PERIOD_PHRASES/etc. are, they're the
raw arithmetic time_segments.py's own tables (MINUTE_SEGMENTS,
HOUR_SEGMENTS, DAY_FRACTIONS) and time_logic/'s resolvers are built
from.
"""

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
# too - time_logic/ uses calendar.monthrange(year, month) when it
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
# time_segments.MONTH_NAMES/datetime.month. February is written as 28
# (the common case, not a leap year) - the one month where "how many
# days" doesn't have a single year-independent answer;
# calendar.monthrange(year, 2) is the exact answer for a specific year
# (see time_logic/), this is the everyday reference value.
MONTH_DAYS = {
    1: 31, 2: 28, 3: 31, 4: 30,
    5: 31, 6: 30, 7: 31, 8: 31,
    9: 30, 10: 31, 11: 30, 12: 31,
}
