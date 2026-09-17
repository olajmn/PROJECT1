"""
One Send on an Active goal card.

Describe → route_note (Planning) → Voice.
Describe and Voice live in llm_roles/; route_note in feedback/.
"""

from backend.llm_roles.describe import describe_in_context
from backend.llm_roles.voice import respond
from backend.manifestation import surface_text, to_planning_node
from backend.planning.feedback.route_note import route_note


def take_turn(latest: dict, note: str) -> dict:
    """One message in → reply out. Same result keys as process_turn(),
    minus capability (always Planning here)."""
    try:
        understanding = describe_in_context(note, _setting(latest))
    except Exception:
        # Describe failure must not drop the note - route_note still
        # has the flags, and the turn is never silently lost.
        understanding = {"about": note}
    record = route_note(latest, note)
    surface = surface_text(record)
    try:
        node = to_planning_node(record)
    except Exception:
        node = None
    reply = respond(note, surface)
    return {
        "record": record,
        "understanding": understanding,
        "surface": surface,
        "node": node,
        "reply": reply,
        "goal_id": record["goal_id"],
    }


def _setting(latest: dict) -> str:
    """Goal + whatever question/suggestion is pending - for Describe only."""
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
