"""Which Fill/replan answer boxes exist (PLAN_KEYS) and which to fill.

Does not own «what time is it» — see time/current_time.py.
Shared by run_stage3.py and reason.py without a circular import.
"""

from backend.foundation.time import broadest_relevant_horizon, resolve_duration

# Defined once. ask() validates the LLM's response has these keys
# (passed in by run_stage3()/replan()).
PLAN_KEYS = (
    "year",
    "month",
    "week",
    "today",
    "hour",
    "minute",
    "now",
)


def _horizon_scope_instruction(duration: str | None) -> str:
    """
    The "fill these horizons in, leave these as null" line, shared by
    run_stage3() and replan() so both compute the boundary the same
    way (see frozen_duration.py §3). `now` is always included in
    fill_keys - it's always the last/narrowest PLAN_KEYS entry, never
    the broadest relevant horizon itself.

    PLAN_KEYS[0] ("year") is a level name, not a literal duration - it
    has no broader horizon above it, so it's the one slot a goal's real
    length can exceed - a 5-year goal is just as "broadest relevant" as
    a 10-month one (see _HORIZON_LENGTH_THRESHOLDS), but the two need
    very different content. When PLAN_KEYS[0] is the broadest, the
    instruction names the goal's own actual resolved span instead of
    leaving the model to assume a literal year.
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
