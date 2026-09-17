"""
The message list on an Active goal card.

Built from saved history - no model call.
"""

from backend.manifestation import surface_text
from backend.planning.goal.resolver import get_history_for_goal


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


def thread_for(goal_id: int, reply: str | None = None) -> list[dict]:
    """Live thread for one goal. When `reply` is the Voice wording from
    the turn just taken, it replaces the last agent line so the card
    shows the voiced sentence rather than the raw surface."""
    messages = thread_messages(get_history_for_goal(goal_id))
    if reply and messages and messages[-1]["role"] == "agent":
        messages[-1] = {"role": "agent", "text": reply}
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
