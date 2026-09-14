"""
One turn of the goal-scoped chat.

Same shape as cli.py's process_turn(), minus Node 3: the caller
already named the goal. LLM2 describes the note in that setting;
route_note() still acts on the raw note (flags on `latest` own the
meaning, not the description); LLM1 voices the deterministic surface.

The description is returned in the trace so a caller can inspect it.
It is not a second router.
"""

# Contents
#  1. Thread from history
#      - thread_messages()
#  2. One turn
#      - take_turn()

from backend.llm1.interface import respond
from backend.manifestation import surface_text, to_planning_node
from backend.planning.chat.understand import understand_note
from backend.planning.feedback.route_note import route_note
from backend.planning.goal.resolver import get_history_for_goal


# ============================================================
# 1. Thread from history
# ============================================================


def thread_messages(history: list[dict]) -> list[dict]:
    """[{role, text}] oldest first - each saved record is one agent
    line (surface_text of its plan); its `feedback`, if any, is the
    user line that produced it. The opening create_goal() record has
    no feedback, so the thread starts with the agent's first question
    or plan.

    Some route_note() branches store a labeled feedback string
    ("Still working on it. Note: still working") rather than the raw
    note. The user line is the note; a repeated surface (check-in that
    didn't change the plan) uses the label as the agent line so the
    thread doesn't print the same next-action twice."""
    messages: list[dict] = []
    previous_surface = None
    for record in history:
        feedback = record.get("feedback")
        if feedback:
            messages.append({"role": "user", "text": _user_line(feedback)})
        surface = surface_text(record)
        agent_text = surface
        if surface == previous_surface:
            ack = _ack_line(feedback)
            if ack:
                agent_text = ack
        messages.append({"role": "agent", "text": agent_text})
        previous_surface = surface
    return messages


def _user_line(feedback: str) -> str:
    marker = " Note: "
    if marker in feedback:
        return feedback.split(marker, 1)[1]
    return feedback


def _ack_line(feedback: str | None) -> str | None:
    if not feedback or " Note: " not in feedback:
        return None
    return feedback.split(" Note: ", 1)[0]


def thread_for(goal_id: int, reply: str | None = None) -> list[dict]:
    """The live thread for one goal. When `reply` is the LLM1 wording
    from the turn just taken, it replaces the last agent line so the
    card shows the voiced sentence rather than the raw surface."""
    messages = thread_messages(get_history_for_goal(goal_id))
    if reply and messages and messages[-1]["role"] == "agent":
        messages[-1] = {"role": "agent", "text": reply}
    return messages


# ============================================================
# 2. One turn
# ============================================================


def take_turn(latest: dict, note: str) -> dict:
    """Parse, route, voice. Returns record/understanding/surface/node/
    reply - same keys process_turn() uses, minus capability (always
    planning here)."""
    try:
        understanding = understand_note(latest, note)
    except Exception:
        # A parser failure must not drop the note - route_note() still
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
