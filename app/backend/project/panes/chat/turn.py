"""
One Send on a Project.

Describe, then Voice. route_note (the plan engine) runs only when the
note is a plan move: a pending question, suggestion, or duration, or
an explicit done / not-done / complete. Otherwise the reply is talk,
and the stored plan is left as it was.

A map node plus a structure request still suggests children from the
chat, instead of calling the plan engine.
"""

from backend.store.data_persistence import save_plan, stamp_map_focus
from backend.agent.llm_roles.describe import describe_in_context
from backend.agent.llm_roles.voice import respond
from backend.agent.manifestation import surface_text, to_planning_node
from backend.project.panes.chat.feedback.feedback_parser import (
    parse_outcome,
    requests_duration_change,
)
from backend.project.panes.chat.feedback.route_note import route_note
from backend.project.panes.canvas.edit_map import suggest_progression_from_chat

_PLAN_OUTCOMES = {"goal_completed", "action_completed", "action_not_completed"}

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
    minus capability (always Planning here).

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
    plan_move = _is_plan_move(latest, note)
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
            record = route_note(latest, note) if plan_move else None
            labels = []
    elif plan_move:
        record = route_note(latest, note)
    else:
        record = None

    if record is None:
        reply = respond(note, _talk_update(map_focus))
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

    if labels:
        listed = "; ".join(labels)
        voice_update = (
            f'Based on what you said about "{map_focus}", I added under '
            f"that node: {listed}. Mention them briefly; invite the user "
            f"to adjust."
        )
    elif map_focus:
        voice_update = (
            f'The user is looking at this node on the project map: '
            f'"{map_focus}". Answer about that node and the project '
            f"around it. Do not push an unrelated first action or "
            f"now-step from the plan. If they seem stuck, you may "
            f"offer to suggest structure under this node — do not "
            f"invent children unless they ask."
        )
    else:
        voice_update = surface

    reply = respond(note, voice_update)
    pid = record["project_id"]
    return {
        "record": record,
        "understanding": understanding,
        "surface": surface,
        "node": node,
        "reply": reply,
        "project_id": pid,
    }


def _is_plan_move(latest: dict, note: str) -> bool:
    """True when this note should go through route_note. Ordinary
    talk returns False and never calls the plan engine."""
    plan = latest.get("plan") or {}
    if (
        plan.get("clarification")
        or plan.get("suggested_action")
        or plan.get("suggested_duration")
        or plan.get("pending_duration_question")
    ):
        return True
    if requests_duration_change(note):
        return True
    return parse_outcome(note) in _PLAN_OUTCOMES


def _talk_update(map_focus: str | None) -> str | None:
    if not map_focus:
        return None
    return (
        f'The user is looking at this node on the project map: '
        f'"{map_focus}". Answer about that node and the project '
        f"around it. Do not push a first action or a now-step."
    )


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
    """Goal + pending question/suggestion + optional map focus —
    for Describe only."""
    goal = latest.get("goal") or ""
    plan = latest.get("plan") or {}
    if plan.get("clarification"):
        pending = f"The agent asked: {plan['clarification']}"
    elif plan.get("suggested_action"):
        pending = f"The agent suggested this first step: {plan['suggested_action']}"
    elif plan.get("suggested_duration"):
        pending = (
            "The agent asked whether the user has a preferred date or "
            "timeframe (saying no / no deadline is fine)"
        )
    elif plan.get("pending_duration_question"):
        pending = f"The agent asked: {plan['pending_duration_question']}"
    else:
        pending = "Nothing is pending - this is an ordinary check-in on the goal."
    parts = [f"The goal is: {goal}", pending]
    if map_focus:
        parts.append(
            f'The user is currently focused on this project-map node: '
            f'"{map_focus}".'
        )
    return "\n".join(parts)
