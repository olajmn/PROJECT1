"""
You send a message, you get a reply back.

Cases:
- A slash-command (`/add`, `/select`, …): chat/commands/ runs it; same save
  path as ordinary Talk (map-writing commands update the tree first).
- Anything else: the model answers, given what
  model/brief/conversation.py puts together.

The message and reply are saved, so the chat is still there after a
reload.
"""

from backend.model.brief.conversation import build_messages
from backend.model.client import send_chat
from backend.storage.paths import now_utc
from backend.storage.project_persistence import save_plan
from backend.project.panes.chat.commands import try_command
from backend.project.panes.create.resolver import get_history_for_project
from backend.project.status.build_status import (
    build_status,
    recent_changes_text,
    status_text,
)


def reply(
    latest: dict,
    note: str,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
    focus_day: str | None = None,
) -> dict:
    """{"record", "select"?, "toggle_map_ids"?} - the saved project
    record the screen is rebuilt from (its thread ends with the reply),
    and what a command asks the UI to do. `focus_day` (YYYY-MM-DD)
    is a selected day of changes; commands ignore it."""
    # Taken before the model is called: the reply can take a while, and
    # the message was sent now, not when the reply is saved.
    sent_at = now_utc()

    commanded = try_command(latest, note, focus_step_id=focus_step_id)
    if commanded is not None:
        text = commanded.reply
        # /select (or path /add with UI focus) frames About-focus.
        stamp_label = commanded.select_label or map_focus
        stamp_id = commanded.select_id or focus_step_id
        base = commanded.record if commanded.record is not None else latest
        record = _save_talk(
            base, note, text, sent_at,
            map_focus=stamp_label, focus_step_id=stamp_id,
        )
        out: dict = {"record": record}
        if commanded.select_id and commanded.select_label:
            out["select"] = {
                "id": commanded.select_id,
                "label": commanded.select_label,
            }
        if commanded.toggle_map_ids:
            out["toggle_map_ids"] = True
        return out

    history = get_history_for_project(latest["project_id"])
    status = "\n\n".join(filter(None, [
        status_text(build_status(history, current=latest)),
        recent_changes_text(history),
    ]))
    messages = build_messages(
        latest, note, history, map_focus, focus_step_id, status,
        focus_day=focus_day,
    )
    text = send_chat(messages).strip()
    record = _save_talk(
        latest, note, text, sent_at,
        map_focus=map_focus, focus_step_id=focus_step_id, focus_day=focus_day,
    )
    return {"record": record}


def _save_talk(
    latest: dict,
    note: str,
    text: str,
    sent_at: str,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
    focus_day: str | None = None,
) -> dict:
    """Keep the map as it is; store the turn as "<reply> Note: <note>",
    the shape screen/chat_thread.py and model/brief/conversation.py read."""
    return save_plan(
        latest.get("name") or "",
        latest.get("plan") or {},
        feedback=f"{text} Note: {note}",
        project_id=latest["project_id"],
        account_id=latest.get("account_id"),
        event="chat",
        sent_at=sent_at,
        map_focus=map_focus,
        focus_step_id=focus_step_id,
        focus_day=focus_day,
    )

