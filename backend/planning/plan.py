"""
Goal -> structured Plan, via a local LLM.

The user writes a goal, a local LLM (via Ollama) generates a plan as
STRUCTURED data (JSON) instead of free text, so the code can later pull
out exactly "what to do right now" instead of the whole plan.

Runs 100% locally - no API key, no internet, no cost.
Requires Ollama running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

Renamed from goal_to_plan.py (2026-08-21) to match the product model in
docs/07-features.md ("Architecture framing: Program / Rooms /
Sitemap") - this file is the "Plan" room. Temporal understanding
(duration parsing/grounding) moved out to backend/foundation/time/, its
own room, in the same pass - see that package's docstring. PLAN_KEYS/
HORIZON_LABELS moved in from storage.py the same day, for the same
reason: they describe the Plan's shape, not anything about how it's
persisted - storage.py never used them internally, only re-exported
them, so this is a clean move with nothing left importing them back.

Run from the PROJECT ROOT: .venv/bin/python -m backend.agent.specialized.plan
"""

import json
from datetime import datetime

import ollama

from backend.foundation.time import broadest_relevant_horizon, resolve_duration, step_count
from backend.infrastructure.data_persistence import save_plan

MODEL = "llama3.1:8b"

# The plan schema, defined once. _ask_model() validates the LLM's
# response has exactly these keys; the templates (via devtools/
# app.py) iterate this same list to render every horizon in order.
PLAN_KEYS = ("one_year", "one_month", "this_week", "today", "this_hour", "this_minute", "right_now")
HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "today": "Today",
    "this_hour": "This hour",
    "this_minute": "This minute",
    "right_now": "Right now",
}

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


# Separate, narrow prompt for _generate_steps() - deliberately NOT
# folded into SYSTEM_PROMPT/one bigger call: the step count itself is
# already decided deterministically (backend/foundation/time/logic/frozen_duration.py's
# step_count()), so the model's only job here is content, never count
# or timing. Only used from generate_plan(), and only when `duration`
# resolves to a real span - see that function. New goals only for now
# (2026-08-21) - replan() doesn't touch steps yet, see
# docs/13-ideas-parking-lot.md's "Plan as an ordered step list" entry
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


def _generate_steps(goal: str, right_now: str, count: int) -> list[str]:
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

    `count` itself always comes from backend/foundation/time/logic/frozen_duration.py's
    step_count(), never from the model. Raises ValueError if the model
    didn't return exactly `count - 1` strings for the remainder, same
    "trust the shape or fail loudly" approach as _ask_model().
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


def _ask_model(system_prompt: str, user_content: str, extra_keys: tuple[str, ...] = ()) -> dict:
    """
    Shared call used by both generate_plan() and replan(): sends a system
    prompt + user message to the local model asking for JSON, parses the
    response, and validates it has the expected plan shape (PLAN_KEYS,
    plus `extra_keys` if the caller's prompt asks for more than that -
    see generate_plan()'s "clarification" key) before handing it back -
    so every caller can trust the shape instead of re-checking it
    themselves.
    """
    response = ollama.chat(
        model=MODEL,
        format="json",  # ask Ollama to constrain output to valid JSON
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    plan = json.loads(response["message"]["content"])

    missing = [key for key in PLAN_KEYS + extra_keys if key not in plan]
    if missing:
        raise ValueError(
            f"Model response is missing required plan key(s) {missing}: {plan}"
        )
    return plan


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
    backend/foundation/time/logic/frozen_duration.py's broadest_relevant_horizon()). Always names
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
    backend/foundation/time/logic/frozen_duration.py's step_count()) - None otherwise (no
    duration given, or free text that isn't grounded in a real span, or
    a clarification question came back instead of a plan). There's
    nothing honest to break into steps without a real timeframe to
    divide - same reasoning DEADLINE_RE's ungrounded deadlines already
    follow elsewhere in this project.
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {resolve_duration(duration)}"
    user_content += _horizon_scope_instruction(duration)
    plan = _ask_model(SYSTEM_PROMPT, user_content, extra_keys=("clarification",))

    plan["steps"] = None
    if plan.get("clarification"):
        return plan
    if duration:
        count = step_count(duration)
        if count is not None:
            plan["steps"] = _generate_steps(goal, plan.get("right_now") or goal, count)
    return plan


def join_plan_prose(texts: list[str]) -> str:
    """
    Join a plan's filled-horizon sentences into one flowing paragraph
    (see devtools/html/active_goal/_plan.html,
    2026-08-23 - horizons used to render as separate labeled lines,
    now as one continuous piece of text). Strips each piece's own
    trailing punctuation/whitespace before re-joining with ". " and a
    final period, rather than a bare space - the model doesn't
    consistently end a horizon's text with a period itself, so a plain
    space-join produces run-on-looking text with no visible sentence
    boundary (e.g. "...long-term Develop a meal planning system...").
    Empty string for an empty list -
    nothing to join, same as the template's own empty check.
    """
    cleaned = [text.strip().rstrip(".") for text in texts if text]
    if not cleaned:
        return ""
    return ". ".join(cleaned) + "."


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
    docs/11-experiments.md.
    """
    # Named history_lines, not "steps" - unrelated to this file's
    # `steps` plan field/_generate_steps() (added later the same day);
    # this is prose lines for the replan prompt, not the step list.
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
    return _ask_model(REPLAN_SYSTEM_PROMPT, user_content)


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
