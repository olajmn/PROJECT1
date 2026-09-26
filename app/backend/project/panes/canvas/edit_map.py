"""
User-authored and zoom writes on a Goal's shadow plan.progression.

add_map_node() — one Step the user named (no LLM), at the
root or under a parent_id.
import_map_outline() — a whole pasted outline/ASCII tree,
parsed by text_to_tree.py (no LLM), appended the same way.
import_map_folder() — one folder on disk, walked by
add_folder/walk.py, appended the same way. Each node keeps its path.
remove_map_node() — drop a Step by id (no LLM).
suggest_map_children() — expand one Step via call_suggest.py
(same is_too_coarse / children_of as the Steps workbench).

Does not touch the Steps-page scratch tree.
"""

import copy
import re

from backend.store.project_persistence import save_plan
from backend.project.panes.canvas.add_folder import folder_tree
from backend.project.panes.canvas.bead import Step, from_labels, from_nested_labels
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.project.panes.canvas.call_suggest import children_from_conversation, zoom_into
from backend.project.panes.create.resolver import get_history_for_project

_ID_NUM = re.compile(r"^p(\d+)$")


def add_map_node(
    latest: dict,
    label: str,
    parent_id: str | None = None,
) -> dict:
    """
    Append one Step the user named — no model call.
    Creates plan.progression if missing. Empty/whitespace label raises.
    If parent_id is set, append under that step's children; otherwise
    at the progression root.
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
    new_step = Step(id=mint(), label=text).to_dict()

    if parent_id:
        found = _find_step(steps, parent_id, ancestors=[])
        if found is None:
            raise ValueError(f"parent step not found: {parent_id}")
        parent, _ancestors = found
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        children.append(new_step)
        feedback = f"Added step under {parent.get('label') or parent_id}: {text}"
    else:
        steps.append(new_step)
        feedback = f"Added step: {text}"

    return save_plan(
        latest["name"],
        plan,
        feedback=feedback,
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="node_added",
    )


def import_map_outline(
    latest: dict,
    text: str | None = None,
    parent_id: str | None = None,
    unwrap: bool = True,
    forest: list[dict] | None = None,
    event: str = "pasted",
) -> dict:
    """
    Parse a pasted outline/ASCII tree (parse_outline.py — markdown
    bullets, numbered lists, this app's own box-drawing export, or
    plain lines) and append the whole result as new Steps — no model
    call, same append-not-replace shape as add_map_node().
    Raises ValueError if nothing recognizable parses out, or if
    parent_id is set but not found.

    `unwrap` (default True) matches parse_outline()'s own parameter -
    the caller should offer this as a user choice (see server.py's
    preview route) rather than always accepting the default guess.

    Exactly one of `text` or `forest` is used: `text` is parsed fresh
    (the chat-Send path, which has no preview step to edit first);
    `forest` is an already-built {"label", "children"} tree the caller
    supplies directly - ui/'s preview builds one of these by toggling
    individual nodes in/out (see outlinePreviewWithToggleableRoot() /
    applyExclusions() in projects.ts), so what gets imported matches
    exactly what the user saw and chose, not a fresh, unedited
    re-parse of the raw text. `unwrap`/`parse_outline()` do not apply
    to a supplied `forest` - it's already the user's final shape.
    """
    if forest is None:
        forest = parse_outline(text or "", unwrap=unwrap)
    else:
        forest = _validate_forest(forest)
    if not forest:
        raise ValueError("no steps recognized in that text")

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
    new_steps = [
        step.to_dict() for step in from_nested_labels(forest, mint)
    ]

    if parent_id:
        found = _find_step(steps, parent_id, ancestors=[])
        if found is None:
            raise ValueError(f"parent step not found: {parent_id}")
        parent, _ancestors = found
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        children.extend(new_steps)
        feedback = f"Imported {len(new_steps)} step(s) under {parent.get('label') or parent_id}"
    else:
        steps.extend(new_steps)
        feedback = f"Imported {len(new_steps)} step(s)"

    return save_plan(
        latest["name"],
        plan,
        feedback=feedback,
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event=event,
    )


def import_map_folder(
    latest: dict,
    folder: str,
    parent_id: str | None = None,
) -> dict:
    """Walk one folder into beads and append them. No model call.
    Same append-not-replace shape as import_map_outline()."""
    return import_map_outline(
        latest,
        parent_id=parent_id,
        forest=folder_tree(folder),
        event="folder_added",
    )


def remove_map_node(latest: dict, step_id: str) -> dict:
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
        latest["name"],
        plan,
        feedback=f"Removed step: {removed_label}",
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="node_removed",
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

def suggest_map_children(latest: dict, step_id: str) -> dict:
    """
    Expand `step_id` one level under latest["plan"]["progression"].
    Appends a new history record with the updated tree.

    If the step is already fine enough (zoom_into returns []), returns
    `latest` unchanged (no save). Raises ValueError if there is no
    progression or no such step. Leftover stored duration is not read.
    """
    plan = latest.get("plan") or {}
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        raise ValueError("goal has no progression tree to zoom")

    new_plan = copy.deepcopy(plan)
    steps = (new_plan.get("progression") or {}).get("steps") or []
    found = _find_step(steps, step_id, ancestors=[])
    if found is None:
        raise ValueError(f"step not found: {step_id}")

    step, ancestors = found
    labels = zoom_into(step["label"], ancestors)
    if not labels:
        return latest

    mint = _id_minter(new_plan["progression"])
    step["children"] = [
        s.to_dict() for s in from_labels(labels, mint)
    ]

    return save_plan(
        latest["name"],
        new_plan,
        feedback=f"Zoomed into: {step['label']}",
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="suggested",
    )


def suggest_map_from_chat(
    latest: dict,
    step_id: str,
    note: str,
    sent_at: str | None = None,
) -> tuple[dict, list[str]]:
    """
    User asked for structure under a focused map node while chatting.
    Proposes children grounded in recent conversation + this note.
    Appends under the node (does not wipe existing children).
    Returns (saved record, new labels). `sent_at` is when the message
    was sent (see save_plan()).
    """
    plan = copy.deepcopy(latest.get("plan") or {})
    progression = plan.get("progression")
    if not isinstance(progression, dict):
        raise ValueError("goal has no progression tree to suggest under")

    steps = (plan.get("progression") or {}).get("steps") or []
    found = _find_step(steps, step_id, ancestors=[])
    if found is None:
        raise ValueError(f"step not found: {step_id}")

    step, ancestors = found
    conversation = _recent_conversation(latest["project_id"], note)
    labels = children_from_conversation(
        step["label"], ancestors, conversation,
    )
    if not labels:
        return latest, []

    mint = _id_minter(plan["progression"])
    existing = step.get("children")
    if not isinstance(existing, list):
        existing = []
        step["children"] = existing
    existing.extend(s.to_dict() for s in from_labels(labels, mint))

    record = save_plan(
        latest["name"],
        plan,
        feedback=note,
        duration=latest.get("duration"),
        project_id=latest["project_id"],
        frozen_duration=latest.get("frozen_duration"),
        current_step=latest.get("current_step", 0),
        sim_user_id=latest.get("sim_user_id"),
        step_status=latest.get("step_status"),
        event="chat_added_nodes",
        sent_at=sent_at,
    )
    return record, labels


def _recent_conversation(project_id: int, latest_note: str, limit: int = 8) -> str:
    """Recent user feedback lines for this goal, plus the current note."""
    lines: list[str] = []
    for record in get_history_for_project(project_id):
        feedback = (record.get("feedback") or "").strip()
        if feedback:
            lines.append(f"User: {feedback}")
    lines = lines[-limit:]
    note = (latest_note or "").strip()
    if note and (not lines or lines[-1] != f"User: {note}"):
        lines.append(f"User: {note}")
    return "\n".join(lines)


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


def _validate_forest(raw: list[dict]) -> list[dict]:
    """A caller-supplied {"label", "children"} tree (ui/'s edited
    preview, not this module's own parse_outline() output) gets the
    same shape check parse_outline() guarantees by construction -
    raises ValueError with a clear reason instead of a raw KeyError/
    TypeError from build() once nesting is already underway."""
    if not isinstance(raw, list):
        raise ValueError("forest must be a list of nodes")
    checked: list[dict] = []
    for node in raw:
        if not isinstance(node, dict):
            raise ValueError("each forest node must be an object")
        label = node.get("label")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("each forest node needs a non-empty label")
        children = node.get("children", [])
        checked_node = {
            "label": label,
            "children": _validate_forest(children),
        }
        path = node.get("path")
        if isinstance(path, str) and path.strip():
            checked_node["path"] = path
        checked.append(checked_node)
    return checked
