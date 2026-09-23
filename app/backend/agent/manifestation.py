"""
UI Manifestation — turning a project record into what a UI can show,
without the UI knowing leftover plan-field names. Pure functions of an
already-saved record; neither calls an LLM or persistence.

- surface_text(): one plain-text sentence about the stored map.
  Leftover planner fields (clarification, suggested_action, now) are
  ignored.
- to_planning_node(): optional {id, label, status, children} tree from
  plan["progression"] only. Bead status is resolved → done, else open.
  Leftover current_step is not read.
"""


def surface_text(record: dict) -> str:
    """One sentence about the stored map. Leftover planner outcomes
    on the same record are not read."""
    steps = _progression_steps(record)
    labels = [
        (step.get("label") or "").strip()
        for step in steps
        if isinstance(step, dict) and (step.get("label") or "").strip()
    ]
    if not labels:
        return "The map is empty."
    listed = ", ".join(labels)
    name = (record.get("goal") or "").strip()
    return f"{name}: {listed}." if name else f"{listed}."


def _progression_steps(record: dict) -> list:
    progression = (record.get("plan") or {}).get("progression")
    if not isinstance(progression, dict):
        return []
    steps = progression.get("steps")
    return steps if isinstance(steps, list) else []


def to_planning_node(record: dict) -> dict | None:
    """{"id", "label", "status", "children"} rooted at the project, or
    None if there is no WHAT progression tree to show."""
    return _node_from_progression(record)


def _node_from_progression(record: dict) -> dict | None:
    """Shadow WHAT tree (plan.progression) — recursive Step dicts."""
    plan = record.get("plan", {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        return None
    steps = progression.get("steps")
    if not isinstance(steps, list) or not steps:
        return None

    children = [
        _progression_step_node(step, i, record["project_id"])
        for i, step in enumerate(steps)
        if isinstance(step, dict)
    ]
    if not children:
        return None

    return {
        "id": f"project-{record['project_id']}",
        "label": record.get("goal", ""),
        "status": "done" if record.get("completed") else "open",
        "children": children,
    }


def _progression_step_node(step: dict, index: int, goal_id: int) -> dict:
    status = "done" if step.get("resolved") else "open"
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
    """Nested beads: status from resolved only."""
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
