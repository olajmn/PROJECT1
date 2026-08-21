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
Sitemap") - this file is the "Plan" room. Timeperiod understanding
(duration parsing/grounding) moved out to backend/timeperiod.py, its
own room, in the same pass - see that module's docstring. PLAN_KEYS/
HORIZON_LABELS moved in from storage.py the same day, for the same
reason: they describe the Plan's shape, not anything about how it's
persisted - storage.py never used them internally, only re-exported
them, so this is a clean move with nothing left importing them back.

Run from the PROJECT ROOT: .venv/bin/python -m backend.plan
"""

import json
from datetime import datetime

import ollama

from backend.storage import save_plan
from backend.timeperiod import _resolve_duration

MODEL = "llama3.1:8b"

# The plan schema, defined once. _ask_model() validates the LLM's
# response has exactly these keys; the templates (via backend/devtools/
# app.py) iterate this same list to render every horizon in order.
PLAN_KEYS = ("one_year", "one_month", "this_week", "right_now")
HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "right_now": "Right now",
}

SYSTEM_PROMPT = (
    "You are a personal execution agent. You will be told the current "
    "date and time, and the user's goal. They may also tell you roughly "
    "how long they want this plan to span (e.g. '30 minutes', 'this "
    "week', '3 months'). Ground everything in the real date/time you "
    "were given - never invent specifics (names, numbers, progress) the "
    "user didn't tell you.\n\n"
    "The plan has four possible horizons, from broadest to narrowest: "
    "one_year, one_month, this_week, right_now. Not every goal deserves "
    "all four - a goal scoped to 45 minutes has no meaningful 'one "
    "year' answer. Decide, based on the goal and the duration you were "
    "given (if any), which horizon is the BROADEST one that's actually "
    "relevant:\n"
    "- Fill in every horizon from that broadest relevant one down "
    "through right_now with a concrete, realistic value.\n"
    "- Set every horizon ABOVE that (broader than relevant) to JSON "
    "null - do not invent a value just to fill the field.\n"
    "- right_now is always filled in, regardless of scope: it's the "
    "single most immediate, concrete action the user can take this "
    "very moment, small enough to start in the next 5 minutes.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly these "
    "four keys - one_year, one_month, this_week, right_now - each "
    "either a string value or JSON null as described above.\n"
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
    "The previous plan already has JSON null on any horizon "
    "(one_year/one_month/this_week) that isn't relevant to this goal's "
    "scope - keep those null unless the feedback clearly means the "
    "goal's scope has grown. Only update the horizons that already had "
    "a real value. right_now is always filled in.\n\n"
    "Respond with ONLY a JSON object (no other text) with exactly the "
    "same keys as before: one_year, one_month, this_week, right_now - "
    "each either a string value or JSON null.\n"
)


def _ask_model(system_prompt: str, user_content: str) -> dict:
    """
    Shared call used by both generate_plan() and replan(): sends a system
    prompt + user message to the local model asking for JSON, parses the
    response, and validates it has the expected plan shape (PLAN_KEYS)
    before handing it back - so every caller can trust the shape instead
    of re-checking it themselves.
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

    missing = [key for key in PLAN_KEYS if key not in plan]
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


def generate_plan(goal: str, duration: str | None = None) -> dict:
    """
    Takes a goal (a text string) and asks the local model to produce a
    structured plan, grounded in the real current date/time. `duration`
    is optional free text from the user (e.g. "30 minutes", "this
    week") describing how far ahead this plan should reach - no fixed
    choices, whatever the user types is passed straight through.
    Returns a dict with keys: one_year, one_month, this_week, right_now.
    """
    user_content = f"The current date and time is: {_now_str()}\n\nMy goal is: {goal}"
    if duration:
        user_content += f"\n\nI want this plan to span roughly: {_resolve_duration(duration)}"
    return _ask_model(SYSTEM_PROMPT, user_content)


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
    several times in a row. Found via real use, 2026-08-20: a goal's
    right_now drifted from "research 4 companies" down to "check the
    news for 30 seconds" over 13 replans, never once advancing toward
    the goal's actual action (sending an application) - see
    docs/11-experiments.md.
    """
    steps = []
    for record in history:
        right_now = record["plan"].get("right_now") or "(none)"
        if record.get("feedback"):
            steps.append(f'- right_now: "{right_now}" -> feedback: "{record["feedback"]}"')
        else:
            steps.append(f'- right_now: "{right_now}" (the first plan, no feedback yet)')
    history_text = "\n".join(steps)

    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My goal is: {goal}\n\n"
        f"This goal's full history so far, oldest first:\n{history_text}\n\n"
        f"My feedback on the most recent 'right_now' action: {feedback}"
    )
    if duration:
        user_content += f"\n\nThis plan should still span roughly: {_resolve_duration(duration)}"
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
