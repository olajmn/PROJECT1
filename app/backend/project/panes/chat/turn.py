"""
One Send on a Project.

Describe, then Voice. Chat is not a plan door. The stored map is
left as it was, except when a focused note asks for structure:
then children are suggested from the chat onto the map.
"""

from backend.store.data_persistence import save_plan, stamp_map_focus
from backend.agent.llm_roles.describe import describe_in_context
from backend.agent.llm_roles.voice import respond
from backend.agent.manifestation import surface_text, to_planning_node
from backend.project.panes.canvas.edit_map import suggest_progression_from_chat
from backend.project.panes.canvas.see_map import focus_labels, map_status
from backend.project.panes.chat.hold import hold_text

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


def take_turn(
    latest: dict,
    note: str,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
) -> dict:
    """One message in → reply out. Result keys match Projects chat
    responses (reply, surface, node, project_id).

    map_focus / focus_step_id: project-map node the user is looking at.
    If they ask for structure while focused, suggest children from chat
    context; otherwise discuss the node without pushing Action/`now`.
    """
    try:
        understanding = describe_in_context(
            note, _setting(latest, map_focus),
        )
    except Exception:
        understanding = {"about": note}

    labels: list[str] = []
    record = None
    if (
        map_focus
        and focus_step_id
        and _asks_for_structure(note)
    ):
        try:
            record, labels = suggest_progression_from_chat(
                latest, focus_step_id, note,
            )
        except Exception:
            record = None
            labels = []

    if record is None:
        reply = respond(
            note,
            _with_hold(
                latest,
                _talk_update(latest, map_focus, focus_step_id),
                map_focus,
                focus_step_id,
            ),
        )
        record = _save_talk(latest, note, reply)
        if map_focus:
            stamped = stamp_map_focus(
                record["project_id"], map_focus, focus_step_id,
            )
            if stamped is not None:
                record = stamped
        try:
            node = to_planning_node(record)
        except Exception:
            node = None
        return {
            "record": record,
            "understanding": understanding,
            "surface": surface_text(record),
            "node": node,
            "reply": reply,
            "project_id": record["project_id"],
        }

    if map_focus:
        stamped = stamp_map_focus(
            record["project_id"], map_focus, focus_step_id,
        )
        if stamped is not None:
            record = stamped

    surface = surface_text(record)
    try:
        node = to_planning_node(record)
    except Exception:
        node = None

    listed = "; ".join(labels)
    voice_update = (
        f'Based on what you said about "{map_focus}", I added under '
        f"that node: {listed}. Mention them briefly; invite the user "
        f"to adjust."
    )
    reply = respond(
        note, _with_hold(latest, voice_update, map_focus, focus_step_id),
    )
    pid = record["project_id"]
    return {
        "record": record,
        "understanding": understanding,
        "surface": surface,
        "node": node,
        "reply": reply,
        "project_id": pid,
    }


def _with_hold(
    latest: dict,
    extra: str,
    map_focus: str | None,
    focus_step_id: str | None,
) -> str:
    prior = hold_text(latest, map_focus, focus_step_id)
    if not prior:
        return extra
    return f"{extra}\n\n{prior}"


def _talk_update(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
) -> str:
    """What Voice may treat as true: the project name and the map."""
    name = (latest.get("goal") or "").strip() or "untitled"
    held = focus_labels(latest, map_focus, focus_step_id)
    parts = [f'This is the open project, labeled: "{name}".']
    if held:
        parts.append(f"The user is looking at this node:\n{held}")
    else:
        parts.append("Its stored map (labels only, source of truth):")
        parts.append(map_status(latest))
    parts.append(
        "You only know these labels and where they sit. "
        "Do not say there is no project. "
        "Do not infer what a file contains or invent a purpose. "
        "Do not dump the whole map unless asked. "
        "Do not push a first action or a now-step."
    )
    return "\n\n".join(parts)


def _save_talk(latest: dict, note: str, reply: str) -> dict:
    """Keep the plan. Store the reply so a reload can show it."""
    return save_plan(
        latest.get("goal") or "",
        latest.get("plan") or {},
        feedback=f"{reply} Note: {note}",
        duration=latest.get("duration"),
        goal_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
    )


def _asks_for_structure(note: str) -> bool:
    text = (note or "").lower()
    return any(cue in text for cue in _STRUCTURE_CUES)


def _setting(latest: dict, map_focus: str | None = None) -> str:
    """Project label and optional map focus — for Describe only."""
    goal = latest.get("goal") or ""
    parts = [f"The goal is: {goal}"]
    if map_focus:
        parts.append(
            f'The user is currently focused on this project-map node: '
            f'"{map_focus}".'
        )
    return "\n".join(parts)
