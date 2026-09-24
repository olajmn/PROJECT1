"""
The message list on an Active goal card.

Built from saved history - no model call.
"""

from backend.agent.translate_nodes import surface_text
from backend.project.panes.create.resolver import get_history_for_goal


def thread_messages(history: list[dict]) -> list[dict]:
    """[{role, text, focus?}] oldest first - each saved record is one
    agent line (surface_text of its map); its `feedback`, if any, is
    the user line that produced it. A mint record has no feedback, so
    the thread starts with the agent's first surface.

    When a turn was map-focused (Talk about this / Looking at), both
    the user and agent lines carry `focus: "<node label>"` (and
    `focus_step_id` when known) so the UI can frame that stretch,
    show where it ends, and re-select the node from the frame.

    Talk turns store a labeled feedback string
    ("<reply> Note: <raw>") rather than the raw note. The user line
    is the note; a repeated surface uses the label as the agent line
    so the thread doesn't print the same line twice."""
    messages: list[dict] = []
    previous_surface = None
    for record in history:
        focus = (record.get("map_focus") or "").strip() or None
        step = (record.get("focus_step_id") or "").strip() or None
        extra: dict = {}
        if focus:
            extra["focus"] = focus
            if step:
                extra["focus_step_id"] = step

        feedback = record.get("feedback")
        if feedback:
            messages.append(
                {"role": "user", "text": _user_line(feedback), **extra},
            )
        surface = surface_text(record)
        agent_text = surface
        if surface == previous_surface:
            ack = _ack_line(feedback)
            if ack:
                agent_text = ack
        messages.append({"role": "agent", "text": agent_text, **extra})
        previous_surface = surface
    return messages


def thread_for(goal_id: int, reply: str | None = None) -> list[dict]:
    """Live thread for one goal. When `reply` is the Voice wording from
    the turn just taken, it replaces the last agent line so the card
    shows the voiced sentence rather than the raw surface."""
    messages = thread_messages(get_history_for_goal(goal_id))
    if reply and messages and messages[-1]["role"] == "agent":
        last = dict(messages[-1])
        last["text"] = reply
        messages[-1] = last
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
