"""
The list of messages shown in the chat panel.

Built from saved chat - no model call. Map edits (add / paste / folder /
Suggest / remove), renames, and archive lines belong in Status, not here
— same rule as model_input/past_turns(). Chat turns and chat that mint
nodes under a focus stay in the thread.
"""

from backend.project.panes.create.resolver import get_history_for_project
from backend.project.timeline import event_name
from backend.store.project_persistence import surface_from_plan

# Saved lines that are not Talk. Status / timeline own these.
_NOT_CHAT = frozenset({
    "node_added",
    "node_removed",
    "pasted",
    "folder_added",
    "suggested",
    "owner_changed",
    "archived",
    "renamed",
})


def thread_messages(history: list[dict]) -> list[dict]:
    """[{role, text, focus?}] oldest first - each saved Talk record is
    one user line (the note) and one agent line (the reply or map
    surface). A mint record has no feedback, so the thread starts with
    the agent's first surface.

    When a turn was map-focused (Talk about this / Looking at), both
    the user and agent lines carry `focus: "<node label>"` (and
    `focus_step_id` when known) so the UI can frame that stretch,
    show where it ends, and re-select the node from the frame.

    Talk turns store a labeled feedback string
    ("<reply> Note: <raw>") rather than the raw note. The user line
    is the note; a repeated surface uses the label as the agent line
    so the thread doesn't print the same line twice.

    Each message carries `at`, when it happened: the agent line the
    record's `created_at`, the user line `sent_at` when saved (chat turns
    since 2026-09-25), else `created_at`."""
    messages: list[dict] = []
    previous_surface = None
    for record in history:
        kind = event_name(record)
        if kind in _NOT_CHAT:
            # Still advance the surface baseline so the next Talk turn
            # does not repeat an unchanged map line as the agent reply.
            previous_surface = surface_text(record)
            continue
        focus = (record.get("map_focus") or "").strip() or None
        step = (record.get("focus_step_id") or "").strip() or None
        extra: dict = {}
        if focus:
            extra["focus"] = focus
            if step:
                extra["focus_step_id"] = step

        created_at = record.get("created_at")
        feedback = record.get("feedback")
        if feedback:
            messages.append({
                "role": "user", "text": _user_line(feedback),
                **_at(record.get("sent_at") or created_at), **extra,
            })
        surface = surface_text(record)
        agent_text = surface
        if surface == previous_surface:
            ack = _ack_line(feedback)
            if ack:
                agent_text = ack
        messages.append(
            {"role": "agent", "text": agent_text, **_at(created_at), **extra},
        )
        previous_surface = surface
    return messages


def thread_for(
    project_id: int,
    reply: str | None = None,
    history: list[dict] | None = None,
) -> list[dict]:
    """Live thread for one goal. When `reply` is the model's wording from
    the turn just taken, it replaces the last agent line so the card
    shows the reply rather than the one-line map summary. Pass `history`
    when the caller already loaded it."""
    if history is None:
        history = get_history_for_project(project_id)
    messages = thread_messages(history)
    if reply and messages and messages[-1]["role"] == "agent":
        last = dict(messages[-1])
        last["text"] = reply
        messages[-1] = last
    return messages


def _at(when: str | None) -> dict:
    """{"at": when}, or nothing when the record has no time."""
    return {"at": when} if when else {}


def _user_line(feedback: str) -> str:
    marker = " Note: "
    if marker in feedback:
        return feedback.split(marker, 1)[1]
    return feedback


def _ack_line(feedback: str | None) -> str | None:
    if not feedback or " Note: " not in feedback:
        return None
    return feedback.split(" Note: ", 1)[0]


def surface_text(record: dict) -> str:
    """One sentence about the stored map.

    Prefers a `surface` string saved on slim events (no full plan on the
    tape). Falls back to building from `plan` on a current record.
    """
    saved = (record.get("surface") or "").strip()
    if saved:
        return saved
    return surface_from_plan(record.get("name") or "", record.get("plan"))
