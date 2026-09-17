"""
Small, direct checks for now(), week_windows(), and day_windows() -
not a test framework, just asserts run top to bottom.

Run from agent/:
    .venv/bin/python -m backend.foundation.time.test_time
"""

# Contents
#  1. now() checks
#  2. week_windows() / day_windows() checks

from datetime import datetime, timedelta

from backend.foundation.time import day_windows, freeze_duration, now, week_windows
from backend.foundation.time.time_logic.frozen_duration import DAYS_PER_WEEK

# 1. now() checks

result = now()
assert isinstance(result, datetime), f"now() returned {type(result)}, expected datetime"
assert result.tzinfo is None, f"now() returned a timezone-aware datetime: {result!r}"
real_now = datetime.now()
assert abs(real_now - result) < timedelta(seconds=5), f"now() = {result}, system clock = {real_now}"
print("OK - now() returns a naive datetime matching the real system clock")

# 2. week_windows() / day_windows() checks

month = freeze_duration("1 month")
windows = week_windows(month)
assert windows is not None, "1 month must be week grain"
assert len(windows) == 4, f"1 month should yield 4 weeks, got {len(windows)}"
assert all("start_label" in w and "end_label" in w for w in windows)
# Calendar weeks start on the span's start date (midnight), not the
# raw freeze instant's clock time.
assert datetime.fromisoformat(windows[0]["start"]).date() == datetime.fromisoformat(month["start"]).date()
assert datetime.fromisoformat(windows[-1]["end"]) == datetime.fromisoformat(month["end"])
print(f"OK - week_windows('1 month') → {len(windows)} weeks "
      f"({windows[0]['start_label']}–{windows[-1]['end_label']})")

four = freeze_duration("4 weeks")
assert len(week_windows(four)) == 4
six = freeze_duration("6 weeks")
assert len(week_windows(six)) == 6
print("OK - week_windows respects N weeks as N candles")

hour = freeze_duration("2 hours")
assert week_windows(hour) is None
print("OK - week_windows('2 hours') is None (session grain)")

year = freeze_duration("1 year")
assert week_windows(year) is None
print("OK - week_windows('1 year') is None (year grain not built here)")

# Days are consecutive calendar dates - no skipped weekdays.
for w in windows[:-1]:
    days = day_windows(w)
    assert len(days) == DAYS_PER_WEEK, f"full week should have {DAYS_PER_WEEK} days, got {len(days)}"
    for i in range(len(days) - 1):
        d0 = datetime.fromisoformat(days[i]["start"]).date()
        d1 = datetime.fromisoformat(days[i + 1]["start"]).date()
        assert d1 - d0 == timedelta(days=1), f"gap in days: {days[i]['start_label']} -> {days[i+1]['start_label']}"

last_days = day_windows(windows[-1])
assert len(last_days) >= DAYS_PER_WEEK
for i in range(len(last_days) - 1):
    d0 = datetime.fromisoformat(last_days[i]["start"]).date()
    d1 = datetime.fromisoformat(last_days[i + 1]["start"]).date()
    assert d1 - d0 == timedelta(days=1)

first = day_windows(windows[0])
print(f"OK - day_windows() consecutive calendar days "
      f"(week 1: {first[0]['start_label']} … {first[-1]['start_label']}; "
      f"last week: {len(last_days)} days)")
