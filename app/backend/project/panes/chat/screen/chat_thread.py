"""
The list of messages shown in the chat panel.

Built from saved chat - no model call. Only Talk turns are shown: a
saved "<reply> Note: <note>" is one user line and one agent line. Map
edits, renames, archive lines, and the project's first record belong
in Status, not here — same rule as model/brief/conversation.past_turns().
"""

from backend.project.panes.create.resolver import get_history_for_project

# Chat turns are saved as "<reply> Note: <user note>" (chat/reply.py).
_NOTE_MARKER = " Note: "


def thread_messages(history: list[dict]) -> list[dict]:
    """[{role, text, focus?}] oldest first - each saved Talk turn is one
    user line (the note) and one agent line (the reply).

    When a turn was map-focused (Talk about this / Looking at), both
    lines carry `focus: "<node label>"` (and `focus_step_id` when known)
    so the UI can frame that stretch, show where it ends, and re-select
    the node from the frame. A turn about a day of changes carries
    `focus_day` (YYYY-MM-DD) instead.

    Each message carries `at`, when it happened: the agent line the
    record's `created_at`, the user line `sent_at` when saved (chat turns
    since 2026-09-25), else `created_at`."""
    messages: list[dict] = []
    for record in history:
        feedback = record.get("feedback") or ""
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


def _at(when: str | None) -> dict:
    """{"at": when}, or nothing when the record has no time."""
    return {"at": when} if when else {}
