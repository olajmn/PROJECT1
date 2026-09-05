"""
Small, direct checks for now() - the Faculty's own authoritative
current-time source (see time_logic/current_time.py). Not a test
framework, just asserts run top to bottom.

Run from the project root:
    .venv/bin/python -m backend.foundation.time.test_time
"""

# Contents
#  1. now() checks
#      - result

from datetime import datetime, timedelta

from backend.foundation.time import now

# 1. now() checks

result = now()
assert isinstance(result, datetime), f"now() returned {type(result)}, expected datetime"

# Naive - no tzinfo - same datetime model the rest of the project
# already uses (see docs/03-architecture.md § Time).
assert result.tzinfo is None, f"now() returned a timezone-aware datetime: {result!r}"

# Actually reads the real system clock (not frozen/hardcoded) - within
# a generous few-second tolerance for however long this script itself
# takes to run.
real_now = datetime.now()
assert abs(real_now - result) < timedelta(seconds=5), f"now() = {result}, system clock = {real_now}"

print("OK - now() returns a naive datetime matching the real system clock")
