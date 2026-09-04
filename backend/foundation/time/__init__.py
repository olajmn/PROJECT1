"""
Understanding "when" a plan should span - free text like "evening",
"30 minutes", or "this month" - grounded in a real clock window or
calendar date range where the code can actually know one, honest about
what it can't. Also a first, narrow sense of what a duration MEANS,
relative to another duration (relative_time.py) - see
docs/03-architecture.md.

A season ("this summer", "next winter") is recognized the same way,
but is a relative, context-dependent concept, not a universal date
range - which months it names depends on hemisphere, which this
project has no concept of yet (see docs/03-architecture.md § Temporal
understanding). resolve_duration()/resolve_span()/describe_duration()
all take an optional `hemisphere` ("northern"/"southern") for exactly
this; a season is reported as recognized but not resolved, never
guessed, when it isn't given one.

data/ - what time IS: time_segments.py (recognized phrases/patterns -
DAY_SEGMENTS, PERIOD_PHRASES, etc.) and time_units.py (raw constants -
SECONDS_PER_MINUTE, MONTH_DAYS, etc.).

now() is the Faculty's own authoritative "current time" - the one
place backend code reads the system clock (`time_logic/__init__.py`),
so every caller shares the same notion of "now" and a later extension
(timezone, a frozen/mocked clock, etc.) only has to change here. Every
current-time read inside this package's own logic/ files goes through
it too, not `datetime.now()` directly.

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
resolve_duration` works regardless of which time_logic/time_data/ file actually
defines it.

Moved 2026-08-25 into this topic-organized backend/foundation/ - full
history: docs/06-development.md, 2026-08-25. See docs/03-architecture.md
§ Faculties for the current design.
"""

from backend.foundation.time.time_logic import now
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
    "now",
    "relative_length",
    "resolve_duration",
    "resolve_span",
    "step_count",
    "step_plan",
    "MAX_STEPS",
    "MIN_STEPS",
    "TARGET_STEP_MINUTES",
]
