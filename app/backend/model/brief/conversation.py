"""
Puts together what the model is sent when you press Send, in order:

1. The system text: the fixed slots from talk_prompt.py, then the
   project background — its summary rows and last changes
   (project/status/; the panel above the chat shows the summary and a
   per-day count instead), every name in its structure, and the part
   or the day of changes you have selected.
2. The earlier chat, as real back-and-forth messages.
3. Your new message.

No model call, nothing saved.
"""

from backend.model.brief.talk_prompt import BEHAVIOR, EXAMPLES, LIMITS, ROLE, TASK
from backend.project.node import path_lines, steps_of, tree_lines
from backend.project.status.build_status import changes_on_day_text, day_name

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
    focus_day: str | None = None,
) -> list[dict]:
    """[{role, content}] for model.client.send_chat(). `status` is the
    project's status text (status/build_status.status_text()).
    `focus_day` (YYYY-MM-DD) is a selected day of changes; that day's
    changes are read from `history`."""
    selected_day = changes_on_day_text(history, focus_day) if focus_day else None
    system = _system_text(latest, map_focus, focus_step_id, status, selected_day)
    messages = [{"role": "system", "content": system}]
    messages.extend(past_turns(history))
    messages.append({"role": "user", "content": _with_focus(note, _focus_tag(map_focus, focus_day))})
    return messages


def past_turns(history: list[dict]) -> list[dict]:
    """Saved chat turns as alternating user/assistant messages, oldest
    first. Map edits and the project's first record carry no chat turn
    and are skipped."""
    turns: list[dict] = []
    for record in history:
        feedback = record.get("feedback") or ""
        if _NOTE_MARKER not in feedback:
            continue
        reply, note = feedback.split(_NOTE_MARKER, 1)
        focus = _focus_tag(record.get("map_focus"), record.get("focus_day"))
        turns.append({"role": "user", "content": _with_focus(note, focus)})
        turns.append({"role": "assistant", "content": reply})
    return turns[-2 * MAX_TURNS:]


def _system_text(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
    status: str | None = None,
    selected_day: str | None = None,
) -> str:
    slots = [
        ("ROLE", ROLE),
        ("TASK", TASK),
        ("BEHAVIOR", BEHAVIOR),
        ("LIMITS", LIMITS),
        ("EXAMPLES", EXAMPLES),
        ("PROJECT BACKGROUND", _background(latest, map_focus, focus_step_id, status, selected_day)),
    ]
    return "\n\n".join(f"{title}\n{text}" for title, text in slots if text)


def _background(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
    status: str | None,
    selected_day: str | None = None,
) -> str:
    """The project as reference for this Send: name, status, map, and
    the selected node or day of changes."""
    name = (latest.get("name") or "").strip() or "untitled"
    parts = [
        "Reference for this conversation; look things up here when the "
        "question needs it.",
        f'Project: "{name}"',
    ]
    if status:
        # Computed from the project's saved changes, so it is fact; the
        # chat below is conversation.
        parts.append(
            "Status (computed from the project's saved changes; treat it "
            "as fact):\n" + status
        )
    steps = steps_of(latest)
    structure = "\n".join(tree_lines(steps)) or "The project has no parts yet."
    parts.append(
        "Structure (names only, each indented under the part it belongs "
        "to):\n" + structure
    )
    # Path from the top down to the selected part; the bare label when
    # the id does not resolve.
    selected = "\n".join(path_lines(steps, focus_step_id)) if focus_step_id else ""
    selected = selected or (map_focus or "").strip()
    if selected:
        parts.append(
            "The user has selected this part (shown with what it sits under "
            "and what it contains):\n" + selected
        )
    elif selected_day:
        parts.append(selected_day)
    else:
        parts.append(
            "Nothing is selected right now; talk about the project as a "
            "whole, not about a part from earlier in the conversation."
        )
    return "\n\n".join(parts)


def _focus_tag(map_focus: str | None, focus_day: str | None) -> str | None:
    """What a turn was about: the node label, or "changes on 27 Sep"."""
    label = (map_focus or "").strip()
    if label:
        return label
    day = (focus_day or "").strip()
    return f"changes on {day_name(day)}" if day else None


def _with_focus(note: str, focus: str | None) -> str:
    """Tags a message with the node it was about, so turns about
    different nodes stay distinguishable in one conversation."""
    return f"[about: {focus}] {note}" if focus else note
