"""
A duration has no fixed meaning as "long" or "short" on its own - only
relative to another duration it's measured against (see
docs/03-architecture.md). "15 minutes" is short next to a full day,
long next to a single minute.

This module answers only "is this span long or short compared to that
span" - pure magnitude. It says nothing about what an activity NEEDS
(a 45-minute run and a 45-minute stretch aren't "the same 45 minutes") -
that's a separate, unbuilt question.
"""

# Contents
#  1. Relative length comparison
#      - _RELATIVE_LENGTH_THRESHOLDS
#      - _span_minutes()
#      - relative_length()

from backend.foundation.time.time_logic.duration_resolution import resolve_span


# 1. Relative length comparison

# Fixed, hardcoded ratio thresholds - not read from anywhere, not
# learned, not model-informed. A reasonable starting convention, not
# derived from any study of duration perception - tune freely if real
# usage shows these bands feel wrong. Checked broadest first, first
# threshold cleared wins.
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
    Is `duration` "short", "medium", or "long" relative to `reference`
    (e.g. the goal's own duration, or the previous step's length) - never
    in absolute terms (see this module's docstring). None if either
    doesn't resolve to a real span, or `reference` resolves to a
    zero-length span (nothing to divide by).
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
