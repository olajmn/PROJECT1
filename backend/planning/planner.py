"""
Planner
=======

Goal -> structured Plan, via a local LLM (Ollama). Produces a plan
across seven time horizons and revises it based on feedback. Never
persists anything itself (see infrastructure/data_persistence.py) and
never talks to the model directly (see model_client.py/step_generator.py).

Contents
1. Plan schema
2. Model prompts
3. Time helpers
4. Plan generation
5. Replanning
6. CLI entry point

Runs 100% locally - no API key, no internet, no cost. Requires Ollama
running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

This file was goal_to_plan.py, then plan.py, then planner.py - "plan"
generates/orchestrates a plan, it doesn't define one, so the agent noun
fits its job better than the domain noun did. HORIZON_LABELS/
join_plan_prose() (presentation), ask_model() (model_client.py), and
generate_steps()/STEPS_SYSTEM_PROMPT (step_generator.py) have all since
moved to their own modules - none of them were Plan-orchestration
itself. PLAN_KEYS stayed - it's genuine Plan shape, passed INTO
ask_model() as a parameter rather than read by it directly, so the
split doesn't create a circular import. Full history:
docs/06-development.md, 2026-08-21/25.

Run from the PROJECT ROOT: .venv/bin/python -m backend.planning.planner
"""

from datetime import datetime

from backend.foundation.time import broadest_relevant_horizon, resolve_duration, step_count
from backend.infrastructure.data_persistence import save_plan
from backend.planning.model_client import ask_model
from backend.planning.step_generator import generate_steps

# ============================================================
# 1. Plan schema
# ============================================================

# Defined once. ask_model() validates the LLM's response has exactly
# these keys (passed in by generate_plan()/replan() below); the
# templates (via devtools/app.py) iterate this same list to render
# every horizon in order.
PLAN_KEYS = ("one_year", "one_month", "this_week", "today", "this_hour", "this_minute", "right_now")

# ============================================================
# 2. Model prompts
# ============================================================

SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time, and the user's goal. They may also tell you roughly "
    "how long they want this plan to span (e.g. '30 minutes', 'this "
    "week', '3 months'). Ground everything in the real date/time you "
    "were given - never invent specifics (names, numbers, progress) the "
    "user didn't tell you.\n\n"
    "First, decide whether the goal as given is specific enough to plan "
    "at all. A bare noun or verb with no object or context (e.g. "
    "'read', 'run', 'work', with nothing else said) isn't - answering it "
    "would mean inventing what book, what distance, what task, none of "
    "which the user actually told you. If so, do NOT invent an answer: "
    "set clarification to ONE short question that would make the goal "
    "specific enough to plan, and set every one of "
    "one_year/one_month/this_week/today/this_hour/this_minute/right_now "
    "to JSON null.\n\n"
    "Otherwise, set clarification to JSON null. The plan has seven "
    "horizons, from broadest to narrowest: one_year, one_month, "
    "this_week, today, this_hour, this_minute, right_now - but not "
    "every goal's real timeframe reaches all the way up to one_year. "
    "You will be told exactly which of these horizons to FILL IN and "
    "which to leave as JSON null, based on the goal's actual given "
    "timeframe - respect that list exactly. Do NOT invent a value for "
    "any horizon you were told to leave null, even a plausible-sounding "
    "one - a goal given '3 months' has no honest one_year answer, "
    "inventing one anyway is fabrication, not planning. For every "
    "horizon you WERE told to fill in, give a concrete, realistic "
    "value, framed as how this goal connects to or fits within that "
    "time window (e.g. a habit it's part of, a pattern it continues, "
    "what stays true a year on, what's realistic to finish today, "
    "within this one hour, within this one minute).\n"
    "- right_now is different from the horizons above it: not a time "
    "window description, but the actual trigger - the single most "
    "immediate, concrete action the user can take this very moment, "
    "small enough to start in the next 5 minutes. Always filled in, "
    "never one of the ones left null.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly these "
    "eight keys - clarification, one_year, one_month, this_week, today, "
    "this_hour, this_minute, right_now - each either a string value or "
    "JSON null as described above.\n"
)

REPLAN_SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time. The user already has a plan for their goal and is "
    "now giving you feedback on whether they completed the most "
    "immediate action ('right_now'). You will also see this goal's "
    "full history: every right_now action tried so far, oldest first, "
    "each with the feedback that followed it - not just the single "
    "most recent step. Adjust the plan based on the latest feedback:\n"
    "- If they did NOT complete it, look at the history first. If "
    "right_now has already been made smaller one or more times without "
    "being completed, do NOT shrink it again - repeatedly shrinking the "
    "same preparatory step is not real progress, and there is no value "
    "in an action smaller than a few minutes. Instead, either directly "
    "address a concrete obstacle they named, or move the action toward "
    "actually attempting the core thing the goal itself names (e.g. if "
    "the goal is 'send 4 applications' and right_now has only ever been "
    "research/browsing, the next right_now should be to actually send "
    "one application, even in the smallest real form - not more "
    "research). Only make right_now smaller the FIRST time it isn't "
    "completed, when the history shows no earlier shrink already "
    "happened.\n"
    "- If they DID complete it, move on to the next logical step.\n\n"
    "Ground everything in the real date/time you were given - never "
    "invent specifics (names, numbers, progress) the user didn't tell "
    "you.\n\n"
    "You will be told exactly which horizons should have a concrete "
    "value and which should be JSON null, same as the previous plan - "
    "this doesn't change on a replan just because the goal's scope "
    "grew in conversation. Never invent a value for a horizon named as "
    "null. Update whichever of the horizons you ARE filling in the "
    "feedback affects; carry the others forward unchanged if the "
    "feedback doesn't touch them.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly the "
    "same keys as before: one_year, one_month, this_week, today, "
    "this_hour, this_minute, right_now - each either a string value or "
    "JSON null.\n"
)


# ============================================================
# 3. Time helpers
# ============================================================


def _now_str() -> str:
    """
    Human-readable current local date and time, e.g. "Wednesday,
    2026-08-19 17:35". Passed to the model on every call so "right now"
    is grounded in the real current moment instead of the model having
    no sense of time at all.
    """
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M")


def _horizon_scope_instruction(duration: str | None) -> str:
    """
    The exact "fill these horizons in, leave these as null" line to
    append to a prompt's user_content - shared by generate_plan() and
    replan() so both ever compute the boundary the same one way (see
    frozen_duration.py §3 - Horizon scoping). Always names
    right_now as one to fill (it's never the broadest relevant horizon
    itself, but the loop below still includes it since it's always the
    last/narrowest PLAN_KEYS entry).
    """
    broadest = broadest_relevant_horizon(duration)
    start = PLAN_KEYS.index(broadest)
    fill_keys = PLAN_KEYS[start:]
    null_keys = PLAN_KEYS[:start]
    instruction = f"\n\nFill in these horizons: {', '.join(fill_keys)}."
    if null_keys:
        instruction += f" Leave these horizons as JSON null: {', '.join(null_keys)}."
    return instruction


# ============================================================
# 4. Plan generation
# ============================================================


def generate_plan(goal: str, duration: str | None = None) -> dict:
    """
    Takes a goal (a text string) and asks the local model to produce a
    structured plan, grounded in the real current date/time. `duration`
    is optional free text from the user (e.g. "30 minutes", "this
    week") describing how far ahead this plan should reach - no fixed
    choices, whatever the user types is passed straight through.
    Returns a dict with keys: clarification, one_year, one_month,
    this_week, right_now, steps.

    `clarification` (added 2026-08-21) is a single question (string)
    instead of a real plan when the goal as given is too vague to plan
    at all - e.g. a bare noun/verb like "read", with no object or
    context (see SYSTEM_PROMPT). Every other key is JSON null in that
    case; callers MUST check `clarification` first and, if it's set,
    treat this as "ask the user again", not as a plan to save - there's
    nothing real in the rest of the dict to act on yet.

    `steps` (added 2026-08-21) is a list of short step descriptions
    only when `duration` actually resolves to a real span (see
    frozen_duration.py §4 - Step planning) - None otherwise (no
    duration given, or free text that isn't grounded in a real span, or
    a clarification question came back instead of a plan). There's
    nothing honest to break into steps without a real timeframe to
    divide - same reasoning DEADLINE_RE's ungrounded deadlines already
    follow elsewhere in this project.

    Does NOT take a `vision_id`/Vision text yet (added 2026-08-26, see
    docs/03-architecture.md § Long-term architecture) - a goal's
    optional Vision is stored (data_persistence.save_plan()'s
    `vision_id`) but not yet supplied to the model here. If/when it is,
    this is the natural place: a caller would resolve `vision_id` to
    its text (data_persistence.get_vision()) and add one short line to
    `user_content` below, the same way `duration` is added - contextual
    framing for the model, never something Vision generates or decides
    on its own (see that doc section: "Vision -> contextualizes Goals",
    not "Vision -> generates every Goal").
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    plan = ask_model(SYSTEM_PROMPT, user_content, PLAN_KEYS + ("clarification",))

    plan["steps"] = None
    if plan.get("clarification"):
        return plan
    if duration:
        count = step_count(duration)
        if count is not None:
            plan["steps"] = generate_steps(goal, plan.get("right_now") or goal, count)
    return plan


# ============================================================
# 5. Replanning
# ============================================================


def replan(goal: str, history: list[dict], feedback: str, duration: str | None = None) -> dict:
    """
    Takes the goal, the goal's full history so far (every record saved
    for it, oldest first - see storage.get_history_for_goal()), and the
    user's feedback on the most recent "right_now" action, then asks the
    model to produce an updated plan. `duration` is the same span
    originally given to generate_plan() (if any) - passed again here so
    the model keeps respecting it on every replan, not just the first
    call. Returns a dict with the same shape as generate_plan().

    Passing the *whole* history (not just the previous plan) is what
    lets REPLAN_SYSTEM_PROMPT's "don't shrink right_now more than once"
    rule actually work - a model only ever shown the single most recent
    step has no way to notice it has already made the same task smaller
    several times in a row. Without it, a goal's right_now can drift -
    e.g. from "research 4 companies" down to "check the news for 30
    seconds" over 13 replans (2026-08-20), never advancing toward the
    goal's actual action (sending an application) - see
    docs/06-development.md.

    Same Vision note as generate_plan() above: not supplied here either yet.
    """
    # Named history_lines, not "steps" - unrelated to this file's
    # `steps` plan field/step_generator.generate_steps() (added later
    # the same day); this is prose lines for the replan prompt, not
    # the step list.
    history_lines = []
    for record in history:
        right_now = record["plan"].get("right_now") or "(none)"
        if record.get("feedback"):
            history_lines.append(f'- right_now: "{right_now}" -> feedback: "{record["feedback"]}"')
        else:
            history_lines.append(f'- right_now: "{right_now}" (the first plan, no feedback yet)')
    history_text = "\n".join(history_lines)

    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My goal is: {goal}\n\n"
        f"This goal's full history so far, oldest first:\n{history_text}\n\n"
        f"My feedback on the most recent 'right_now' action: {feedback}"
    )
    if duration:
        user_content += f"\n\nThis plan should still span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    return ask_model(REPLAN_SYSTEM_PROMPT, user_content, PLAN_KEYS)


# ============================================================
# 6. CLI entry point
# ============================================================

# Only runs when this file is executed directly
# (not when other files import functions from it)
if __name__ == "__main__":
    my_goal = input("What do you want to achieve? ")
    print("\nThinking...\n")
    plan = generate_plan(my_goal)

    for horizon, text in plan.items():
        print(f"{horizon}: {text}")

    record = save_plan(my_goal, plan)
    print(f"\n[Saved as entry #{record['id']} in data/plans.json]")
