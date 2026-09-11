"""
Generate a plan's step content, one model call - each step optionally
carrying its own microsteps, so a small goal reads as a plain step
list and a large one reads as steps with detail underneath, using the
same shape for both rather than two different data models.

How many meaningfully distinct steps (and microsteps) a goal needs is
a judgment about its actual complexity and domain (climbing Everest
and tidying a desk are both "long" by the clock, but nowhere near
equally complex) - not something a duration-only formula can answer
honestly. This project's usual "code decides, the model is told" split
(see docs/03-architecture.md § Faculty, shape b) applies to genuinely
deterministic, unambiguous arithmetic (duration math, quantity); step
count for a plan is neither - it's the same kind of contextual
judgment the rest of this file already trusts the model for. See
docs/05-decisions.md for the 2026-09-11 entry removing the previous
time-formula approach (foundation/time/time_logic/frozen_duration.py's
old step_count(), MIN_STEPS=3/MAX_STEPS=6) once it was shown to
collapse to a flat constant for nearly every real goal - any span over
~2 hours produced exactly 6 steps regardless of actual scope.

Deliberately ONE call, not two - an earlier two-call version (a
separate structure decision, then step_generator.py's own separate
content call) measurably destabilized the second call's output
against the local model (backend/reasoning/model_client.py); folding
both into a single response removes that risk rather than working
around it. step_generator.py is retired - this module fully replaces
it.

Second version (2026-09-11): dropped the first version's separate
"flat"/"phases" flag - it duplicated information the step shape itself
already carries (a step with microsteps IS a phase; one without is a
plain step), and its first live test showed exactly this confusion:
asked to choose "phases", the model still had nowhere to put grouped
content, so it forced everything into one long flat list instead. One
step shape, used uniformly, removes the ambiguity.
"""

import json

from backend.reasoning.model_client import send_message
from backend.foundation.time import resolve_span

# A safety ceiling only - guards against a malformed/degenerate
# response (e.g. a runaway list), not a target range the model should
# aim for. Applied separately to the top-level step count and to any
# one step's microstep count.
MAX_SANE_STEPS = 20
MAX_SANE_MICROSTEPS = 20

STEPS_SYSTEM_PROMPT = (
    "You are planning a goal's steps. Given the goal, its first step "
    "(already fixed - you never rewrite or rephrase it), and how long "
    "the plan spans, produce however many further steps actually make "
    "sense for this goal - not a fixed count. Continue in order after "
    "the given first step, and together with it, plausibly accomplish "
    "the goal. Do not repeat the first step, and do not repeat any "
    "step you already produced.\n\n"
    "Each step may optionally have its own microsteps - smaller, "
    "concrete actions that make up that one step. Use microsteps only "
    "where a step is genuinely substantial enough to warrant breaking "
    "down further (e.g. a whole phase of a large goal, like "
    "\"prepare climbing gear\"); leave microsteps as an empty list for "
    "an already-concrete step (e.g. \"drink the water\") - do not "
    "invent microsteps just to fill the field. A short goal should end "
    "up with plain steps and no microsteps anywhere; a large or "
    "complex goal should end up with microsteps under its bigger "
    "steps.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly one "
    "key, \"steps\", whose value is a JSON array of objects, each with "
    "exactly two keys: \"label\" (a short string) and \"microsteps\" "
    "(a JSON array of short strings, possibly empty)."
)


def generate_structure(goal: str, duration: str, right_now: str) -> dict | None:
    """
    {"steps": [{"label": str, "microsteps": [str, ...]}, ...]} - the
    first step's `label` is always `right_now` itself, unchanged, with
    an empty `microsteps` list, exactly like
    step_generator.generate_steps() used to guarantee (see that
    module's history) - never a second, independently-worded idea of
    "the first action" from the model. None if `duration` doesn't
    resolve to a real span at all (nothing to plan steps against).

    Raises ValueError if the model's response doesn't have the
    expected shape - same "trust the shape or fail loudly" approach as
    model_client.ask_model()/the retired step_generator.py.
    """
    if resolve_span(duration) is None:
        return None

    user_content = (
        f"My goal is: {goal}\n\n"
        f"The first step, already decided, is: {right_now}\n\n"
        f"The plan spans: {duration}"
    )
    raw = send_message(STEPS_SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > MAX_SANE_STEPS:
        raise ValueError(f"Model did not return a sane step list: {data}")
    for step in steps:
        if (
            not isinstance(step, dict)
            or not isinstance(step.get("label"), str)
            or not isinstance(step.get("microsteps"), list)
            or len(step["microsteps"]) > MAX_SANE_MICROSTEPS
            or not all(isinstance(m, str) for m in step["microsteps"])
        ):
            raise ValueError(f"Model did not return a sane step shape: {data}")

    first = {"label": right_now, "microsteps": []}
    return {"steps": [first] + steps}
