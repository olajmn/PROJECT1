"""
You send a message, you get a reply back.

Cases:
- A slash-command (`/project_summary`, `/add`, …): chat/commands/ runs it; same save
  path as ordinary Talk (map-writing commands update the tree first).
- A node is selected and the message asks for ideas ("suggest",
  "brainstorm", ...): new child nodes are added under it
  (canvas/edit_map.py does the adding). The reply says what was added.
- Anything else: the model answers, given what
  model/brief/conversation.py puts together.

The message and reply are saved, so the chat is still there after a
reload.
"""

from backend.model.brief.conversation import build_messages
from backend.model.client import send_chat
from backend.storage.paths import now_utc
from backend.storage.project_persistence import save_plan
from backend.project.panes.canvas.edit_map import suggest_map_from_chat
from backend.project.panes.chat.commands import try_command
from backend.project.panes.create.resolver import get_history_for_project
from backend.project.status.build_status import build_status, status_text

# User is asking for ideas / structure under the focused node.
_STRUCTURE_CUES = (
    "suggest",
    "suggestion",
    "propose",
    "come up with",
    "make 3",
    "make three",
    "make two",
    "make 2",
    "ideas for",
    "structure under",
    "break down",
    "brainstorm",
    "concepts within",
    "add concepts",
    "generate",
    "what could",
    "foreslå",
    "forslag",
    "ideer",
)


def reply(
    latest: dict,
    note: str,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
) -> dict:
    """{"record", "reply"} - the saved project record the screen is
    rebuilt from, and the reply text to show."""
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
        out = {"record": record, "reply": text}
        if commanded.select_id and commanded.select_label:
            out["select"] = {
                "id": commanded.select_id,
                "label": commanded.select_label,
            }
        return out

    if map_focus and focus_step_id and _asks_for_structure(note):
        try:
            record, labels = suggest_map_from_chat(
                latest,
                focus_step_id,
                note,
                sent_at=sent_at,
                map_focus=map_focus,
                focus_step_id=focus_step_id,
            )
        except Exception:
            record, labels = None, []
        if labels:
            text = f'Added under "{map_focus}": {", ".join(labels)}.'
            return {"record": record, "reply": text}

    history = get_history_for_project(latest["project_id"])
    status = status_text(build_status(history, current=latest))
    messages = build_messages(latest, note, history, map_focus, focus_step_id, status)
    text = send_chat(messages).strip()
    record = _save_talk(
        latest, note, text, sent_at,
        map_focus=map_focus, focus_step_id=focus_step_id,
    )
    return {"record": record, "reply": text}


def _save_talk(
    latest: dict,
    note: str,
    text: str,
    sent_at: str,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
) -> dict:
    """Keep the map as it is; store the turn as "<reply> Note: <note>",
    the shape screen/chat_thread.py and model/brief/conversation.py read."""
    return save_plan(
        latest.get("name") or "",
        latest.get("plan") or {},
        feedback=f"{text} Note: {note}",
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="chat",
        sent_at=sent_at,
        map_focus=map_focus,
        focus_step_id=focus_step_id,
    )


def _asks_for_structure(note: str) -> bool:
    text = (note or "").lower()
    return any(cue in text for cue in _STRUCTURE_CUES)
