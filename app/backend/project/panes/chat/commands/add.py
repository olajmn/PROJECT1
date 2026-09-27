"""/add — mint a child node under focus or under a named path.

No model. Uses edit_map.add_map_node. Parse:

- `/add child` + focus_step_id → under the selected node
- `/add Parent / Child` → under Parent (first label match)
- `/add A / B / Child` → walk A → B, add Child under B
"""

from backend.project.panes.canvas.edit_map import add_map_node
from backend.project.node.tree_as_text import find_step
from backend.project.panes.chat.commands.node_path import (
    args_after_command,
    id_at_path,
    path_segments,
    slash_path_error,
    steps_of,
)
from backend.project.panes.chat.commands.result import CommandResult

_USAGE = (
    "Usage: /add child (with a node selected), "
    "or /add Parent / Child (path ok: A / B / Child)."
)


def run(
    latest: dict,
    note: str,
    focus_step_id: str | None = None,
) -> CommandResult:
    args = args_after_command(note)
    if not args:
        return CommandResult(_USAGE)
    bad = slash_path_error(args)
    if bad:
        return CommandResult(bad)

    parent_id, child, err = _resolve(latest, args, focus_step_id)
    if err:
        return CommandResult(err)
    assert parent_id is not None and child is not None
    try:
        record = add_map_node(latest, child, parent_id=parent_id)
    except ValueError as exc:
        return CommandResult(str(exc))

    parent = find_step(steps_of(latest), parent_id) or {}
    parent_label = (parent.get("label") or parent_id).strip() or parent_id
    # The saved label may carry a " (2)" suffix if a sibling had `child`.
    saved = (find_step(steps_of(record), parent_id) or {}).get("children") or []
    added = saved[-1].get("label", child) if saved else child
    return CommandResult(
        reply=f'Added under "{parent_label}": {added}.',
        record=record,
    )


def _resolve(
    latest: dict,
    args: str,
    focus_step_id: str | None,
) -> tuple[str | None, str | None, str | None]:
    """(parent_id, child_label, error)."""
    segments = path_segments(args)
    if len(segments) >= 2:
        *path_labels, child = segments
        parent_id = id_at_path(steps_of(latest), path_labels)
        if parent_id is None:
            shown = " / ".join(path_labels)
            return None, None, f'No node at path "{shown}".'
        return parent_id, child, None

    child = args.strip()
    if not child:
        return None, None, _USAGE
    wanted = (focus_step_id or "").strip()
    if not wanted:
        return None, None, _USAGE
    if find_step(steps_of(latest), wanted) is None:
        return None, None, f"Focused node not found: {wanted}"
    return wanted, child, None
