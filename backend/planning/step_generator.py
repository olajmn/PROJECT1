"""
Turn a goal's already-decided first step into a full ordered step
list, via a second, narrower model call.

Split out of planner.py (formerly plan.py) as its own module,
2026-08-27.
"""

import json

import ollama

from backend.planning.model_client import MODEL

# Separate, narrow prompt for generate_steps() - deliberately NOT
# folded into planner.py's SYSTEM_PROMPT/one bigger call: the step
# count itself is already decided deterministically
# (backend/foundation/time/time_logic/frozen_duration.py's
# step_count()), so the model's only job here is content, never count
# or timing. Only used from planner.generate_plan(), and only when
# `duration` resolves to a real span - see that function. New goals
# only for now (2026-08-21) - replan() doesn't touch steps yet, see
# docs/06-development.md's "Plan as an ordered step list" entry
# for the open questions (multi-horizon step lists, what happens to
# steps on replan) still to work out before extending this further.
STEPS_SYSTEM_PROMPT = (
    "You are continuing a goal's plan. Its first step is already fixed "
    "and given to you exactly as written - you never rewrite or "
    "rephrase it. Your only job is to produce the steps that come "
    "AFTER it: a fixed number of further short, specific, realistic "
    "actions, continuing in order, that together with the first step "
    "would plausibly accomplish the goal. Do not repeat the first "
    "step, and do not repeat any step you already produced.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly one "
    "key, \"steps\", whose value is a JSON array of exactly the "
    "requested number of short strings - ONLY the steps after the "
    "first one, in the order they should be done.\n"
)


def generate_steps(goal: str, right_now: str, count: int) -> list[str]:
    """
    `count` short step descriptions, step 1 ALWAYS being `right_now`
    itself, unchanged - never a second, independently-worded idea of
    "the first action" from the model. Only steps 2..count are an
    actual model call (see STEPS_SYSTEM_PROMPT).

    Without this (2026-08-21): the model's own idea of "the first
    concrete action" (asked for as context, not fixed) can come out
    worded differently from - and overlap awkwardly with - right_now
    itself, so Task (right now) and the step list visibly disagree
    (e.g. steps 2-3 re-covering what right_now already said, step 4
    repeating step 1's idea). Fixing step 1 to be the
    literal same string removes the disagreement structurally, instead
    of trying to word a prompt carefully enough to avoid it.

    `count` itself always comes from backend/foundation/time/time_logic/frozen_duration.py's
    step_count(), never from the model. Raises ValueError if the model
    didn't return exactly `count - 1` strings for the remainder, same
    "trust the shape or fail loudly" approach as model_client.ask_model().
    """
    if count <= 1:
        return [right_now]
    remaining = count - 1
    user_content = (
        f"My goal is: {goal}\n\n"
        f"The first step, already decided, is: {right_now}\n\n"
        f"Produce exactly {remaining} further steps, after that one."
    )
    response = ollama.chat(
        model=MODEL,
        format="json",
        messages=[
            {"role": "system", "content": STEPS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    data = json.loads(response["message"]["content"])
    steps = data.get("steps")
    if not isinstance(steps, list) or len(steps) != remaining or not all(isinstance(s, str) for s in steps):
        raise ValueError(f"Model did not return exactly {remaining} step strings: {data}")
    return [right_now] + steps
