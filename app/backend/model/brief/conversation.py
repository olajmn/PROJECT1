"""
Puts together what the model is sent when you press Send, in order:

1. An intro text: the project's status (the same text shown above the
   chat — project/status/), every label on the map, and the node you
   have selected.
2. The earlier chat, as real back-and-forth messages.
3. Your new message.

No model call, nothing saved.
"""

from backend.model.brief.map_context import focus_labels, map_status

# Earlier turns kept per Send. Bounds prompt size on a local model;
# older turns stay saved and shown, just not re-sent.
MAX_TURNS = 20

# Chat turns are saved as "<reply> Note: <user note>" (reply.py).
_NOTE_MARKER = " Note: "


def build_messages(
    latest: dict,
    note: str,
    history: list[dict],
    map_focus: str | None = None,
    focus_step_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """[{role, content}] for model.client.send_chat(). `status` is the
    project's status text (status/build_status.status_text())."""
    messages = [
        {"role": "system", "content": _system_text(latest, map_focus, focus_step_id, status)},
    ]
    messages.extend(past_turns(history))
    messages.append({"role": "user", "content": _with_focus(note, map_focus)})
    return messages


def past_turns(history: list[dict]) -> list[dict]:
    """Saved chat turns as alternating user/assistant messages, oldest
    first. Map edits and the project's first record carry no Talk turn
    and are skipped."""
    turns: list[dict] = []
    for record in history:
        feedback = record.get("feedback") or ""
        if _NOTE_MARKER not in feedback:
            continue
        reply, note = feedback.split(_NOTE_MARKER, 1)
        focus = (record.get("map_focus") or "").strip() or None
        turns.append({"role": "user", "content": _with_focus(note, focus)})
        turns.append({"role": "assistant", "content": reply})
    return turns[-2 * MAX_TURNS:]


def _system_text(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
    status: str | None = None,
) -> str:
    name = (latest.get("name") or "").strip() or "untitled"
    parts = [
        "You are talking with the user about one of their projects. "
        "The project is shown to them as a map of labeled nodes.",
        f'Project: "{name}"',
    ]
    if status:
        # Computed from the project's saved changes, so it is fact; the
        # chat below is conversation. The user sees the same text.
        parts.append(
            "Project status (computed from its saved changes — treat it as "
            "fact; the user sees the same text above the chat):\n" + status
        )
    parts.append("The map (labels only):\n" + map_status(latest))
    selected = focus_labels(latest, map_focus, focus_step_id)
    if selected:
        parts.append("The user has selected this node (path from the top):\n" + selected)
    # The model only ever receives labels; without this it describes
    # file contents it has never seen.
    parts.append(
        "You only see these labels, not what is inside any file or "
        "folder they name."
    )
    return "\n\n".join(parts)


def _with_focus(note: str, focus: str | None) -> str:
    """Tags a message with the node it was about, so turns about
    different nodes stay distinguishable in one conversation."""
    return f"[about: {focus}] {note}" if focus else note
