"""Map context for Talk — indented labels (and focus path) the model
gets on Send.

Only reads the map, never changes it. No model call."""

from backend.project.node.tree_as_text import (
    path_lines,
    tree_lines,
)


def map_status(latest: dict) -> str:
    """Every stored label as indented tree text. Empty map is said
    plainly."""
    lines = tree_lines(_steps(latest))
    if not lines:
        return "The map is empty."
    return "\n".join(lines)


def focus_labels(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
) -> str | None:
    """Path from the top down to the selected node, or None when
    nothing is selected."""
    if focus_step_id:
        lines = path_lines(_steps(latest), focus_step_id)
        if lines:
            return "\n".join(lines)
    return (map_focus or "").strip() or None


def _steps(latest: dict) -> list:
    steps = ((latest.get("plan") or {}).get("progression") or {}).get("steps")
    return steps if isinstance(steps, list) else []
