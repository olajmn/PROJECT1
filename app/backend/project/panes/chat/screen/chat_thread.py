"""
The list of messages shown in the chat panel.

Built from saved chat - no model call. Chat turns are shown: a saved
"<reply> Note: <note>" is one user line and one agent line. One kind of
map edit also shows, as a quiet note: renaming a node that has been
talked about, inside that node's conversation, so earlier turns that use
the old name still make sense (docs/05-decisions.md #71). Other map
edits, archive lines, and the project's first record belong in Status,
not here — same rule as model/brief/conversation.past_turns().
"""

from backend.project.panes.create.resolver import get_history_for_project

# Chat turns are saved as "<reply> Note: <user note>" (chat/reply.py).
_NOTE_MARKER = " Note: "

# A node rename is saved as "Renamed step: <old> → <new>"
# (panes/canvas/edit_map.rename_map_node()).
_RENAME_PREFIX = "Renamed step: "
_RENAME_ARROW = " → "


def thread_messages(history: list[dict]) -> list[dict]:
    """[{role, text, focus?}] oldest first - each saved chat turn is one
    user line (the note) and one agent line (the reply).

    When a turn was map-focused (Talk about this / Looking at), both
    lines carry `focus: "<node label>"` (and `focus_step_id` when known)
    so the UI can frame that stretch, show where it ends, and re-select
    the node from the frame. A turn about a day of changes carries
    `focus_day` (YYYY-MM-DD) instead.

    Each message carries `at`, when it happened: the agent line the
    record's `created_at`, the user line `sent_at` when saved (chat turns
    since 2026-09-25), else `created_at`.

    A rename of a node that has chat turns becomes one `role: "note"`
    line with that node's `focus_step_id` and its new label as `focus`."""
    talked_about = {
        (r.get("focus_step_id") or "").strip()
        for r in history
        if _NOTE_MARKER in (r.get("feedback") or "")
    } - {""}
    messages: list[dict] = []
    for record in history:
        feedback = record.get("feedback") or ""
        note_line = _rename_note(record, talked_about)
        if note_line:
            messages.append(note_line)
            continue
        if _NOTE_MARKER not in feedback:
            continue
        reply, note = feedback.split(_NOTE_MARKER, 1)
        focus = (record.get("map_focus") or "").strip() or None
        step = (record.get("focus_step_id") or "").strip() or None
        extra: dict = {}
        day = (record.get("focus_day") or "").strip() or None
        if focus:
            extra["focus"] = focus
            if step:
                extra["focus_step_id"] = step
        elif day:
            extra["focus_day"] = day
        created_at = record.get("created_at")
        messages.append({
            "role": "user", "text": note,
            **_at(record.get("sent_at") or created_at), **extra,
        })
        messages.append({"role": "agent", "text": reply, **_at(created_at), **extra})
    return messages


def thread_for(project_id: int, history: list[dict] | None = None) -> list[dict]:
    """Live thread for one project. Pass `history` when the caller
    already loaded it."""
    if history is None:
        history = get_history_for_project(project_id)
    return thread_messages(history)


def _rename_note(record: dict, talked_about: set[str]) -> dict | None:
    """The quiet "Renamed from … to …" line for a node rename, or None
    when the record is not one or the node was never talked about."""
    if record.get("event") != "node_renamed":
        return None
    step = (record.get("focus_step_id") or "").strip()
    feedback = record.get("feedback") or ""
    if step not in talked_about or not feedback.startswith(_RENAME_PREFIX):
        return None
    old, sep, new = feedback[len(_RENAME_PREFIX):].partition(_RENAME_ARROW)
    if not sep:
        return None
    return {
        "role": "note",
        "text": f"Renamed from “{old}” to “{new}”",
        "focus": new,
        "focus_step_id": step,
        **_at(record.get("created_at")),
    }


def _at(when: str | None) -> dict:
    """{"at": when}, or nothing when the record has no time."""
    return {"at": when} if when else {}
