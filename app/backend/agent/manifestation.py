"""
UI Manifestation (docs/v4-migration-decision.md) - turning a Planning result
into what a UI can show, without Planning knowing anything about UI
concerns and without the UI knowing Planning's own field names
(PLAN_KEYS, step_status, current_step, ...). This is the first
concrete home for the "UI manifestation" layer docs/v4-migration-decision.md
names but leaves unspecified - filled in only as far as Planning's
actual result shape requires, not as a general framework.

Two translations, deliberately kept separate and both pure functions
of an already-existing Planning record - neither calls Planning, an
LLM, or persistence:

- surface_text(): the ONE plain-text sentence Voice is allowed to see
  and relay conversationally (see backend.agent.llm_roles.voice). Same
  precedence current/'s _active_goal/_conversation.html chat thread
  already uses.
- to_planning_node(): an OPTIONAL, generic {id, label, status,
  children} tree. Prefers shadow plan["progression"] (WHAT Step tree)
  when present; otherwise falls back to legacy plan["steps"] /
  step_status / current_step. Callers get None when neither exists.
"""

from backend.foundation.time import step_plan as _step_plan


def surface_text(record: dict) -> str:
    """The one plain-text summary of a Planning record - see module
    docstring."""
    plan = record.get("plan", {})
    if plan.get("clarification"):
        return plan["clarification"]
    if plan.get("suggested_action"):
        return plan["suggested_action"]
    if plan.get("suggested_duration"):
        # Older records may still store an invented span here; ask
        # openly instead of confirming that guess.
        return (
            "Do you have a preferred date or timeframe to finish this "
            "within? (You can also say no / no deadline.)"
        )
    if plan.get("pending_duration_question"):
        return plan["pending_duration_question"]
    if plan.get("now"):
        return plan["now"]
    return "(no next action came back - give feedback again, or mark complete)"


def to_planning_node(record: dict) -> dict | None:
    """{"id", "label", "status", "children"} rooted at the Goal, or
    None if there is no progression/steps tree to show."""
    from_progression = _node_from_progression(record)
    if from_progression is not None:
        return from_progression
    return _node_from_legacy_steps(record)


def _node_from_progression(record: dict) -> dict | None:
    """Shadow WHAT tree (plan.progression) — recursive Step dicts."""
    plan = record.get("plan", {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        return None
    steps = progression.get("steps")
    if not isinstance(steps, list) or not steps:
        return None

    current_index = record.get("current_step", 0)
    if not isinstance(current_index, int) or current_index < 0:
        current_index = 0

    children = [
        _progression_step_node(step, i, current_index, record["goal_id"])
        for i, step in enumerate(steps)
        if isinstance(step, dict)
    ]
    if not children:
        return None

    return {
        "id": f"goal-{record['goal_id']}",
        "label": record.get("goal", ""),
        "status": "done" if record.get("completed") else "current",
        "children": children,
    }


def _progression_step_node(
    step: dict, index: int, current_index: int, goal_id: int,
) -> dict:
    if step.get("resolved"):
        status = "done"
    elif index == current_index:
        status = "current"
    else:
        status = "open"
    step_id = step.get("id") or f"{goal_id}-p-{index}"
    nested = step.get("children") or []
    return {
        "id": str(step_id),
        "label": step.get("label") or "—",
        "status": status,
        "children": [
            _progression_child_node(child, step_id, j)
            for j, child in enumerate(nested)
            if isinstance(child, dict)
        ],
    }


def _progression_child_node(step: dict, parent_id: str, index: int) -> dict:
    """Nested progression steps: status from resolved only (no
    current_step pointer below the top level yet)."""
    status = "done" if step.get("resolved") else "open"
    step_id = step.get("id") or f"{parent_id}-{index}"
    nested = step.get("children") or []
    return {
        "id": str(step_id),
        "label": step.get("label") or "—",
        "status": status,
        "children": [
            _progression_child_node(child, step_id, j)
            for j, child in enumerate(nested)
            if isinstance(child, dict)
        ],
    }


def _node_from_legacy_steps(record: dict) -> dict | None:
    """Legacy calendar/session plan.steps (two-level dicts)."""
    plan = record.get("plan", {})
    steps = plan.get("steps")
    if not steps:
        return None

    current_index = record.get("current_step", 0)
    status_list = record.get("step_status")
    if not status_list or len(status_list) != len(steps):
        status_list = ["open"] * len(steps)

    # Prefer dates already stored on week-grain steps; otherwise even-
    # slice the frozen span across the label list (session grain).
    timed = _step_plan(record.get("frozen_duration"), steps)

    children = []
    for i, step in enumerate(steps):
        if status_list[i] == "resolved":
            status = "done"
        elif i == current_index:
            status = "current"
        else:
            status = "open"
        label = f"{timed[i]['start_label']}–{timed[i]['end_label']}: {step['label']}" if timed else step["label"]
        children.append({
            "id": f"{record['goal_id']}-step-{i}",
            "label": label,
            "status": status,
            # One level deep only - week-grain days are dated dicts;
            # session microsteps are plain strings. Microsteps are
            # always "open": no per-microstep completion signal today.
            "children": [
                _microstep_child(record["goal_id"], i, j, microstep)
                for j, microstep in enumerate(step.get("microsteps") or [])
            ],
        })

    return {
        "id": f"goal-{record['goal_id']}",
        "label": record.get("goal", ""),
        "status": "done" if record.get("completed") else "current",
        "children": children,
    }


def _microstep_child(goal_id: int, step_i: int, micro_j: int, microstep) -> dict:
    if isinstance(microstep, dict):
        text = microstep.get("label") or "—"
        sl, el = microstep.get("start_label"), microstep.get("end_label")
        if isinstance(sl, str) and isinstance(el, str):
            label = f"{sl}: {text}" if sl == el else f"{sl}–{el}: {text}"
        else:
            label = text
    else:
        label = microstep
    return {
        "id": f"{goal_id}-step-{step_i}-micro-{micro_j}",
        "label": label,
        "status": "open",
        "children": [],
    }
