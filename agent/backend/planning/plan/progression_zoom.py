"""
User-authored and zoom writes on a Goal's shadow plan.progression.

add_progression_bead() — one top-level Step the user named (no LLM).
remove_progression_bead() — drop a Step by id (no LLM).
zoom_progression_step() — expand one Step via planning/plan/zoom.py
(same is_too_coarse / children_of as the Steps workbench).

Does not touch the Steps-page scratch tree.
"""

import copy
import re

from backend.infrastructure.data_persistence import save_plan
from backend.planning.plan.zoom import zoom_into

_ID_NUM = re.compile(r"^p(\d+)$")


def add_progression_bead(latest: dict, label: str) -> dict:
    """
    Append one top-level Step the user named — no model call.
    Creates plan.progression if missing. Empty/whitespace label raises.
    """
    text = (label or "").strip()
    if not text:
        raise ValueError("step label is empty")

    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        progression = {"steps": []}
        plan["progression"] = progression
    steps = progression.get("steps")
    if not isinstance(steps, list):
        steps = []
        progression["steps"] = steps

    mint = _id_minter(progression)
    steps.append(
        {
            "id": mint(),
            "label": text,
            "ordered": True,
            "resolved": False,
            "children": [],
        }
    )

    return save_plan(
        latest["goal"],
        plan,
        feedback=f"Added step: {text}",
        duration=latest.get("duration"),
        goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"),
        step_status=latest.get("step_status"),
    )


def remove_progression_bead(latest: dict, step_id: str) -> dict:
    """
    Remove `step_id` from plan.progression (top-level or nested).
    No model call. Raises if missing progression or step.
    """
    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        raise ValueError("goal has no progression tree")
    steps = progression.get("steps")
    if not isinstance(steps, list):
        raise ValueError("goal has no progression tree")

    removed_label = _remove_step(steps, step_id)
    if removed_label is None:
        raise ValueError(f"step not found: {step_id}")

    if not steps:
        plan["progression"] = None

    return save_plan(
        latest["goal"],
        plan,
        feedback=f"Removed step: {removed_label}",
        duration=latest.get("duration"),
        goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"),
        step_status=latest.get("step_status"),
    )


def _remove_step(steps: list, step_id: str) -> str | None:
    """Delete the dict with id==step_id from this list or a nested
    children list. Returns its label, or None if not found."""
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        if step.get("id") == step_id:
            label = str(step.get("label") or step_id)
            del steps[i]
            return label
        nested = step.get("children")
        if isinstance(nested, list):
            found = _remove_step(nested, step_id)
            if found is not None:
                return found
    return None


def zoom_progression_step(latest: dict, step_id: str) -> dict:
    """
    Expand `step_id` one level under latest["plan"]["progression"].
    Appends a new history record with the updated tree.

    If the step is already fine enough (zoom_into returns []), returns
    `latest` unchanged (no save). Raises ValueError if there is no
    progression or no such step. Timeframe is optional grounding —
    missing duration no longer blocks expand (co-build without a span).
    """
    plan = latest.get("plan") or {}
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        raise ValueError("goal has no progression tree to zoom")

    duration = latest.get("duration")
    if not duration:
        frozen = latest.get("frozen_duration") or {}
        duration = frozen.get("text")
    if not duration:
        # Same soft context construct_progression uses: span is
        # background, not a gate. Zoom still needs *some* string for
        # the model preamble in zoom._describe_position.
        duration = (
            "no fixed timeframe — a few next units of work only, "
            "not a full syllabus"
        )

    new_plan = copy.deepcopy(plan)
    steps = (new_plan.get("progression") or {}).get("steps") or []
    found = _find_step(steps, step_id, ancestors=[])
    if found is None:
        raise ValueError(f"step not found: {step_id}")

    step, ancestors = found
    labels = zoom_into(step["label"], ancestors, duration)
    if not labels:
        return latest

    mint = _id_minter(new_plan["progression"])
    step["children"] = [
        {
            "id": mint(),
            "label": label,
            "ordered": True,
            "resolved": False,
            "children": [],
        }
        for label in labels
    ]

    return save_plan(
        latest["goal"],
        new_plan,
        feedback=f"Zoomed into: {step['label']}",
        duration=latest.get("duration"),
        goal_id=latest["goal_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        vision_id=latest.get("vision_id"),
        step_status=latest.get("step_status"),
    )


def _find_step(
    steps: list, step_id: str, ancestors: list[str],
) -> tuple[dict, list[str]] | None:
    for step in steps:
        if not isinstance(step, dict):
            continue
        if step.get("id") == step_id:
            return step, list(ancestors)
        nested = _find_step(
            step.get("children") or [],
            step_id,
            ancestors=[*ancestors, step.get("label") or ""],
        )
        if nested is not None:
            return nested
    return None


def _id_minter(progression: dict):
    used = {0}

    def walk(nodes: list) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            match = _ID_NUM.match(str(node.get("id") or ""))
            if match:
                used.add(int(match.group(1)))
            walk(node.get("children") or [])

    walk(progression.get("steps") or [])
    counter = {"n": max(used)}

    def mint() -> str:
        counter["n"] += 1
        return f"p{counter['n']}"

    return mint
