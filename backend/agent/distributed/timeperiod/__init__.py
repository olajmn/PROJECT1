"""
Understanding "when" a plan should span - free text like "evening",
"30 minutes", or "this month" - grounded in a real clock window or
calendar date range where the code can actually know one, honest about
what it can't.

The recognized phrases/patterns themselves (DAY_SEGMENTS, PERIOD_PHRASES,
etc.) live in backend/agent/distributed/timesegments.py, not here - this package is the
logic that resolves and describes them. Originally one file
(backend/agent/distributed/timeperiod.py, split out of goal_to_plan.py 2026-08-21 to
match the product model in docs/07-features.md - "Timeperiod is its
own room"); turned into this package 2026-08-24, once the file had
grown to three genuinely different layers doing three different jobs:

- matchers.py - recognize a known phrase in free text, turn it into
  hard values (hours, dates, offsets), using backend/agent/distributed/timesegments.py's
  pattern tables.
- resolve.py - three parallel views over the same matched phrase
  (resolve_duration/resolve_span/describe_duration), built on
  matchers.py.
- frozen.py - the "frozen duration" lifecycle (freeze once at goal
  creation, read back unchanged on every later render) and everything
  built on top of a frozen span: progress bars, step slicing, horizon
  scoping.

Every name below is re-exported here so nothing outside this package
needs to know it's a package rather than a single file - `from
backend.agent.distributed.timeperiod import resolve_duration` keeps working exactly as
before the split.

Future hook (not built yet, see docs/12-decisions.md, 2026-08-21 and
docs/08-technical-architecture.md § Memory & Data Architecture, and
docs/13-ideas-parking-lot.md's 2026-08-24 "semantic understanding of
time" entry): this package is where a real year -> month -> week ->
day -> hour -> minute hierarchy, or a genuinely semantic sense of what
a duration MEANS (not just converts to), would eventually live, if/
when flat duration strings and raw minute-counting stop being enough -
e.g. a `resolve_hierarchy()` alongside today's `resolve_duration()`,
walking a structured scale instead of matching free text. Deliberately
not started now - only day/week/month/year phrase recognition and flat
numeric duration live here today, not a real walkable hierarchy or any
notion of what an amount of time means in context.
"""

from backend.agent.distributed.timeperiod.frozen import (
    MAX_STEPS,
    MIN_STEPS,
    TARGET_STEP_MINUTES,
    broadest_relevant_horizon,
    duration_progress,
    freeze_duration,
    step_count,
    step_plan,
)
from backend.agent.distributed.timeperiod.matchers import extract_duration_phrase
from backend.agent.distributed.timeperiod.resolve import describe_duration, resolve_duration, resolve_span

__all__ = [
    "broadest_relevant_horizon",
    "describe_duration",
    "duration_progress",
    "extract_duration_phrase",
    "freeze_duration",
    "resolve_duration",
    "resolve_span",
    "step_count",
    "step_plan",
    "MAX_STEPS",
    "MIN_STEPS",
    "TARGET_STEP_MINUTES",
]
