"""
MVP v0.2 - "Goal -> Structured Plan"

The user writes a goal, a local LLM (via Ollama) generates a plan as
STRUCTURED data (JSON) instead of free text, so the code can later pull
out exactly "what to do right now" instead of the whole plan.

Runs 100% locally - no API key, no internet, no cost.
Requires Ollama running in the background (start with: brew services start ollama)
and the model pulled (ollama pull llama3.1:8b).

Run from the PROJECT ROOT: .venv/bin/python -m backend.goal_to_plan
"""

import json
import re
from datetime import datetime

import ollama

from backend.storage import PLAN_KEYS, save_plan

MODEL = "llama3.1:8b"

# Recognized day segments: word -> (start_hour, end_hour) in 24h local
# time, both in [0, 24). "night"/"natt" wraps past midnight (23 -> 6),
# handled specially in _resolve_duration(). This is the code actually
# *knowing* what "evening" means (a real clock window) instead of
# handing the raw word to the model and hoping it guesses sensibly -
# see docs/11-experiments.md, 2026-08-19.
DAY_SEGMENTS = {
    "morning": (6, 12),
    "morgen": (6, 12),
    "formiddag": (6, 12),
    "afternoon": (12, 17),
    "ettermiddag": (12, 17),
    "evening": (17, 23),
    "kveld": (17, 23),
    "tonight": (17, 23),
    "night": (23, 6),
    "natt": (23, 6),
}

# A plain "N minutes/hours/days" phrase - the other case the code can
# actually understand (a real, countable span), rather than a day
# segment or fully open text. Doesn't do anything with the number yet
# beyond recognizing it as understood; see docs/13-ideas-parking-lot.md
# for using it to compute a real deadline later.
_DURATION_LENGTH_RE = re.compile(
    r"\b(\d+)\s*(minute|minutt|hour|time|day|dag)s?\b", re.IGNORECASE
)

# A deadline tied to a personal routine event, not a clock time - found
# via real test usage 2026-08-19 ("any time before i got to bed", see
# docs/11-experiments.md). Deliberately NOT given the same treatment as
# DAY_SEGMENTS: there's no real, known clock time to compute (we don't
# track when the user actually goes to bed), so resolving this to a
# fake hour would be inventing grounding that doesn't exist. Recognized
# only so describe_duration() can say what it honestly is - a same-day
# deadline with an unknown clock time - instead of lumping it in with
# genuinely unexamined free text.
#
# A regex, not a fixed phrase list: the first real test hit "before i
# got to bed" - a fixed list of exact phrases missed that variation
# ("got to" vs "go to"/"bed" alone). \w* around the verb tolerates
# go/going/got/getting; "to" and "i" are optional so "before bed" alone
# still matches too.
_DEADLINE_RE = re.compile(
    r"before\s+(?:i\s+)?(?:\w+\s+to\s+)?(bed(?:time)?|sleep)"
    r"|f(?:ø|oe)r\s+(?:jeg\s+)?legger\s+meg"
    r"|innen\s+(?:jeg\s+)?legger\s+meg",
    re.IGNORECASE,
)


def _matched_day_segment(duration: str) -> tuple[str, tuple[int, int]] | None:
    """Return (word, (start_hour, end_hour)) for the first known day
    segment found in `duration`, or None if none match."""
    lowered = duration.lower()
    for word, hours in DAY_SEGMENTS.items():
        if word in lowered:
            return word, hours
    return None


def _matched_deadline_phrase(duration: str) -> str | None:
    """Return the actual matched text if `duration` names a routine-
    event deadline (see _DEADLINE_RE), or None if none match."""
    match = _DEADLINE_RE.search(duration)
    return match.group(0) if match else None


def _resolve_duration(duration: str | None) -> str | None:
    """
    Ground `duration` in a real clock window when it's a recognized day
    segment (see DAY_SEGMENTS), so the model is told an actual time
    range instead of just the word "evening". Anything that isn't a
    recognized segment - a plain length ("30 minutes") or fully open
    text ("before my trip") - is passed through unchanged; the model
    still has to interpret those itself, same as before.
    """
    if not duration:
        return duration

    match = _matched_day_segment(duration)
    if match is None:
        return duration

    word, (start, end) = match
    today = datetime.now().strftime("%Y-%m-%d")
    if start < end:
        window = f"{start:02d}:00-{end:02d}:00"
    else:
        window = f"{start:02d}:00-{end:02d}:00 (past midnight)"
    return f"{duration} (resolved: today {today}, {window})"


def describe_duration(duration: str | None) -> str:
    """
    One-line explanation of how `duration` was understood, for display
    next to it in the UI (see index.html / _plan_entry.html) - so it's
    visible whether the code actually grounded this in a real clock
    window (a day segment) or is just passing the raw text to the model
    unexamined (a length like "30 minutes", or fully open text).
    """
    if not duration:
        return ""
    match = _matched_day_segment(duration)
    if match:
        word, (start, end) = match
        return f'given, resolved by code: "{word}" = {start:02d}:00-{end:02d}:00'
    deadline = _matched_deadline_phrase(duration)
    if deadline:
        return f'given, recognized as a same-day deadline ("{deadline}") - actual time unknown, not grounded'
    if _DURATION_LENGTH_RE.search(duration):
        return "given, recognized as a length, not grounded in a clock time"
    return "given, not parsed/verified by code"

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
    "immediate action ('right_now'). Adjust the plan based on this "
    "feedback:\n"
    "- If they did NOT complete it, make the next right_now action "
    "smaller and easier, or address the obstacle they mentioned.\n"
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


def replan(goal: str, previous_plan: dict, feedback: str, duration: str | None = None) -> dict:
    """
    Takes the goal, the previous structured plan, and the user's feedback
    on the previous "right_now" action, and asks the model to produce an
    updated plan. `duration` is the same span originally given to
    generate_plan() (if any) - passed again here so the model keeps
    respecting it on every replan, not just the first call. Returns a
    dict with the same shape as generate_plan().
    """
    user_content = (
        f"The current date and time is: {_now_str()}\n\n"
        f"My goal is: {goal}\n\n"
        f"The previous plan was: {json.dumps(previous_plan)}\n\n"
        f"My feedback on the 'right_now' action: {feedback}"
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
