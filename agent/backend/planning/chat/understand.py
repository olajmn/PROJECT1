"""
LLM2 for a note that already belongs to a Goal.

Builds the setting (the goal text, plus whichever question or
suggestion is pending on the latest record) and hands it to
llm2.understand_in_context(). Still no decision - route_note.py owns
which branch runs, from the record's flags, not from this description.
"""

from backend.llm2.parser import understand_in_context


def setting_for(latest: dict) -> str:
    """Plain-language framing for the parser - what is already hanging
    on this goal, if anything. Not shown to the user; LLM1 never sees
    it."""
    goal = latest.get("goal") or ""
    plan = latest.get("plan") or {}
    if plan.get("clarification"):
        pending = f"The agent asked: {plan['clarification']}"
    elif plan.get("suggested_action"):
        pending = f"The agent suggested this first step: {plan['suggested_action']}"
    elif plan.get("suggested_duration"):
        pending = (
            f"The agent proposed {plan['suggested_duration']} as the timeframe"
        )
    elif plan.get("pending_duration_question"):
        pending = f"The agent asked: {plan['pending_duration_question']}"
    else:
        pending = "Nothing is pending - this is an ordinary check-in on the goal."
    return f"The goal is: {goal}\n{pending}"


def understand_note(latest: dict, note: str) -> dict:
    """{"about": ...} for `note` read against `latest`, not in a vacuum."""
    return understand_in_context(note, setting_for(latest))
