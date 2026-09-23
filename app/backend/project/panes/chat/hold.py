"""Prior chat lines Voice may hold this turn.

No model. No write. The list comes from thread.py — the same
messages the screen already shows. This file only cuts them to a
short block of text.

Focused turns hold only that node's lines. Unfocused turns hold
only project-wide lines. The two do not mix.
"""

from backend.project.panes.chat.thread import thread_messages
from backend.project.panes.create.resolver import get_history_for_goal

MAX_MESSAGES = 12
MAX_CHARS = 400


def hold_text(
    latest: dict,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
) -> str | None:
    """Earlier lines in this scope, or None when there are none."""
    pid = latest.get("project_id")
    if pid is None:
        return None
    messages = scope_hold(
        thread_messages(get_history_for_goal(int(pid))),
        map_focus,
        focus_step_id,
    )
    return format_hold(messages, focused=bool(map_focus or focus_step_id))


def scope_hold(
    messages: list[dict],
    map_focus: str | None,
    focus_step_id: str | None,
) -> list[dict]:
    """Keep only the lines that belong to this turn's scope."""
    step = (focus_step_id or "").strip()
    label = (map_focus or "").strip()
    if step:
        return [
            message for message in messages
            if (message.get("focus_step_id") or "").strip() == step
        ]
    if label:
        return [
            message for message in messages
            if (message.get("focus") or "").strip() == label
        ]
    return [message for message in messages if not message.get("focus")]


def format_hold(messages: list[dict], focused: bool = False) -> str | None:
    """Last messages as a Voice block. Long lines are cut."""
    if not messages:
        return None
    lines: list[str] = []
    for message in messages[-MAX_MESSAGES:]:
        who = "User" if message.get("role") == "user" else "Agent"
        text = " ".join(str(message.get("text") or "").split())
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "…"
        if text:
            lines.append(f"{who}: {text}")
    if not lines:
        return None
    heading = (
        "Earlier lines about this node:"
        if focused
        else "Earlier lines in this project's chat:"
    )
    return (
        heading + "\n"
        + "\n".join(lines)
        + "\nTreat these as already said. Do not invent older talk."
        + (
            " Do not bring in talk about other nodes."
            if focused
            else " Do not bring in talk that was about a selected node."
        )
    )
