"""
The "DNA" of duration understanding (see docs/03-architecture.md): a
duration has no fixed meaning as "long" or "short" on its own - only
ever relative to some other duration it's being measured against. "15
minutes" isn't short or long in itself; it's short next to a full day,
long next to a single minute.

Deliberately narrow, matching the scope decided for this module's
first version: this says nothing about what an activity NEEDS (a
45-minute run and a 45-minute stretch are not "the same 45 minutes") -
that's a separate, harder, still-unbuilt question (see the doc's
"activity-specific meaning" open question), closer to a Language/
Semantics faculty than to Time. This module answers only "is this SPAN
long or short compared to THAT span" - pure magnitude, no knowledge of
what either span is FOR.
"""

from backend.foundation.time.time_logic.duration_resolution import resolve_span


# Fixed, hardcoded ratio thresholds - not read from anywhere, not
# learned, not model-informed. The same "code decides" instinct
# _HORIZON_LENGTH_THRESHOLDS in frozen_duration.py already applies to a
# different question (which horizon is broad enough to fill in)
# applied here to a different one (is this span long or short next to
# its reference). Convention over precision, same trade-off as
# WEEKS_PER_MONTH elsewhere in this package: a reasonable starting
# default, not derived from any study of duration perception - tune
# freely once real usage shows these bands feel wrong. Checked
# broadest-first, first threshold cleared wins.
_RELATIVE_LENGTH_THRESHOLDS = (
    ("long", 0.5),
    ("medium", 0.15),
    ("short", 0.0),
)


def _span_minutes(duration: str | None) -> float | None:
    """Total length of `duration`'s resolved span, in minutes - None if
    it doesn't resolve to a real span at all (see resolve_span())."""
    span = resolve_span(duration)
    if span is None:
        return None
    start, end = span
    return (end - start).total_seconds() / 60


def relative_length(duration: str | None, reference: str | None) -> str | None:
    """
    Is `duration` "short", "medium", or "long" - not on its own (there
    is no such thing, see this module's docstring), but relative to
    `reference` (e.g. the goal's own overall duration, or the previous
    step's length). None if either doesn't resolve to a real span, or
    `reference` resolves to a zero-length span (nothing to divide by) -
    nothing grounded to compare, same honesty as every other "not
    parsed/verified by code" case in this package.
    """
    duration_minutes = _span_minutes(duration)
    reference_minutes = _span_minutes(reference)
    if duration_minutes is None or reference_minutes is None or reference_minutes <= 0:
        return None
    ratio = duration_minutes / reference_minutes
    for label, min_ratio in _RELATIVE_LENGTH_THRESHOLDS:
        if ratio >= min_ratio:
            return label
    return "short"  # pragma: no cover - defensive; the 0.0 threshold above already catches everything
