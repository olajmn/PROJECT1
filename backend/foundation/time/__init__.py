"""
Understanding "when" a plan should span - free text like "evening",
"30 minutes", or "this month" - grounded in a real clock window or
calendar date range where the code can actually know one, honest about
what it can't. Also a first, narrow sense of what a duration MEANS,
relative to another duration (relative_time.py) - see
docs/14-semantic-time.md.

data/ - what time IS: time_segments.py (recognized phrases/patterns -
DAY_SEGMENTS, PERIOD_PHRASES, etc.) and time_units.py (raw constants -
SECONDS_PER_MINUTE, MONTH_DAYS, etc.).

logic/ - what acts on that data:
- phrase_matching.py - recognize a known phrase in free text, turn it
  into hard values (hours, dates, offsets), using data/time_segments.py's
  pattern tables.
- duration_resolution.py - three parallel views over the same matched
  phrase (resolve_duration/resolve_span/describe_duration), built on
  phrase_matching.py.
- frozen_duration.py - the "frozen duration" lifecycle (freeze once at
  goal creation, read back unchanged on every later render) and
  everything built on top of a frozen span: progress bars, step
  slicing, horizon scoping.
- relative_time.py - is one duration short/medium/long relative to
  another (e.g. the goal's overall length) - deterministic, no
  knowledge of what either span is FOR (see its own docstring).

Every name below is re-exported here so nothing outside this package
needs to know its internal shape - `from backend.foundation.time import
resolve_duration` works regardless of which logic/data/ file actually
defines it.

Moved 2026-08-25 from backend/agent/distributed/temporal/ (itself
renamed from timeperiod/ earlier the same day) - out of agent/
entirely, into this topic-organized backend/foundation/, replacing the
narrow/broad specialized//distributed/ reuse split with one folder per
subject. See docs/08-technical-architecture.md § Faculties (due for an
update to match - not yet rewritten as of this move).
"""

from backend.foundation.time.time_logic.frozen_duration import (
    MAX_STEPS,
    MIN_STEPS,
    TARGET_STEP_MINUTES,
    broadest_relevant_horizon,
    duration_progress,
    freeze_duration,
    step_count,
    step_plan,
)
from backend.foundation.time.time_logic.phrase_matching import extract_duration_phrase
from backend.foundation.time.time_logic.relative_time import relative_length
from backend.foundation.time.time_logic.duration_resolution import describe_duration, resolve_duration, resolve_span

__all__ = [
    "broadest_relevant_horizon",
    "describe_duration",
    "duration_progress",
    "extract_duration_phrase",
    "freeze_duration",
    "relative_length",
    "resolve_duration",
    "resolve_span",
    "step_count",
    "step_plan",
    "MAX_STEPS",
    "MIN_STEPS",
    "TARGET_STEP_MINUTES",
]
