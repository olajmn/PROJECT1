"""
Translate a saved project record into what UI and Voice may see.

No LLM. No persistence. Leftover planner fields on the record are
not read — only the stored map (`plan.progression`).
"""

# Contents
#  1. Surface text
#      - surface_text()
#
#  2. Map tree
#      - to_planning_node()


# ============================================================
# 1. Surface text
# ============================================================


def surface_text(record: dict) -> str:
    """One sentence about the stored map."""
    labels = [
        (step.get("label") or "").strip()
        for step in _top_steps(record)
        if isinstance(step, dict) and (step.get("label") or "").strip()
    ]
    if not labels:
        return "The map is empty."
    listed = ", ".join(labels)
    name = (record.get("goal") or "").strip()
    return f"{name}: {listed}." if name else f"{listed}."


def _top_steps(record: dict) -> list:
    progression = (record.get("plan") or {}).get("progression")
    if not isinstance(progression, dict):
        return []
    steps = progression.get("steps")
    return steps if isinstance(steps, list) else []


# ============================================================
# 2. Map tree
# ============================================================


def to_planning_node(record: dict) -> dict | None:
    """{"id", "label", "status", "children"} rooted at the project,
    or None when there is no progression tree to show.

    Bead status is resolved → done, else open.
    """
    progression = (record.get("plan") or {}).get("progression")
    if not isinstance(progression, dict):
        return None
    steps = progression.get("steps")
    if not isinstance(steps, list) or not steps:
        return None

    children = [
        _bead_node(step, i, record["project_id"])
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


def _bead_node(step: dict, index: int, project_id: int) -> dict:
    step_id = step.get("id") or f"{project_id}-p-{index}"
    nested = step.get("children") or []
    return {
        "id": str(step_id),
        "label": step.get("label") or "—",
        "status": _bead_status(step),
        "children": [
            _child_bead(child, step_id, j)
            for j, child in enumerate(nested)
            if isinstance(child, dict)
        ],
    }


def _child_bead(step: dict, parent_id: str, index: int) -> dict:
    step_id = step.get("id") or f"{parent_id}-{index}"
    nested = step.get("children") or []
    return {
        "id": str(step_id),
        "label": step.get("label") or "—",
        "status": _bead_status(step),
        "children": [
            _child_bead(child, step_id, j)
            for j, child in enumerate(nested)
            if isinstance(child, dict)
        ],
    }


def _bead_status(step: dict) -> str:
    return "done" if step.get("resolved") else "open"
