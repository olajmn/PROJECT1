"""
Plan shape and shared prompt-grounding helpers.

PLAN_KEYS and the time lines generate_plan()/replan() both need -
kept here so generate_plan.py (Stage 3) and planner.py can share
them without a circular import.
"""

from backend.foundation.time import broadest_relevant_horizon, now, resolve_duration

# Defined once. ask_model() validates the LLM's response has exactly
# these keys (passed in by generate_plan()/replan()); templates that
# iterate horizons use the same list.
PLAN_KEYS = (
    "year",
    "month",
    "week",
    "today",
    "hour",
    "minute",
    "now",
)


def _now_str() -> str:
    """Grounds the model's "right now" in the real current moment - it has no other sense of time."""
    return now().strftime("%A, %Y-%m-%d %H:%M")


def _horizon_scope_instruction(duration: str | None) -> str:
    """
    The "fill these horizons in, leave these as null" line, shared by
    generate_plan() and replan() so both compute the boundary the same
    way (see frozen_duration.py §3). `now` is always included in
    fill_keys - it's always the last/narrowest PLAN_KEYS entry, never
    the broadest relevant horizon itself.

    PLAN_KEYS[0] ("year") is a level name, not a literal duration - it
    has no broader horizon above it, so it's the one slot a goal's real
    length can exceed - a 5-year goal is just as "broadest relevant" as
    a 10-month one (see _HORIZON_LENGTH_THRESHOLDS), but the two need
    very different content. When PLAN_KEYS[0] is the broadest, the
    instruction names the goal's own actual resolved span instead of
    leaving the model to assume a literal year (SYSTEM_PROMPT's framing
    example talks about "that goal's own outer horizon" for the same
    reason).
    """
    broadest = broadest_relevant_horizon(duration)
    start = PLAN_KEYS.index(broadest)
    fill_keys = PLAN_KEYS[start:]
    null_keys = PLAN_KEYS[:start]
    instruction = f"\n\nFill in these horizons: {', '.join(fill_keys)}."
    if null_keys:
        instruction += f" Leave these horizons as JSON null: {', '.join(null_keys)}."
    if broadest == PLAN_KEYS[0]:
        instruction += (
            f" This goal's own actual outer timeframe is {resolve_duration(duration)} - "
            f"describe the '{PLAN_KEYS[0]}' horizon around that real timeframe, not "
            "literally one calendar year, whenever it's longer or shorter than that."
        )
    return instruction
