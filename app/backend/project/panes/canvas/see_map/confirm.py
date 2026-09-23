"""When the user asks to see the map, the reply is the stored labels.

No model. Voice does not rewrite this. Selecting a node does not
dump the list by itself — that only happens on the phrases below.
"""

from backend.project.panes.canvas.read_map.outline import (
    outline_lines,
    path_lines,
)

# This node (and its path). Needs a selection to be useful.
_THIS_CUES = (
    "what is this",
    "what's this",
    "what's here",
    "what is here",
    "hva er dette",
    "hva er her",
)

# The whole stored map.
_MAP_CUES = (
    "what do you see",
    "what you see",
    "what's on the map",
    "what is on the map",
    "hva ser du",
    "hva ligger",
)


def asks_to_see(note: str) -> bool:
    return _has(note, _THIS_CUES) or _has(note, _MAP_CUES)


def confirm_text(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
    note: str,
) -> str | None:
    """The stored labels, or None when this turn is not a confirm."""
    steps = _steps(latest)
    if _has(note, _THIS_CUES):
        if focus_step_id:
            lines = path_lines(steps, focus_step_id)
            if lines:
                return "\n".join(lines)
            if map_focus:
                return map_focus
        lines = outline_lines(steps)
        return "\n".join(lines) if lines else "The map is empty."
    if _has(note, _MAP_CUES):
        lines = outline_lines(steps)
        return "\n".join(lines) if lines else "The map is empty."
    return None


def map_status(latest: dict) -> str:
    """The stored labels Voice may hold. Empty map is said plainly."""
    lines = outline_lines(_steps(latest))
    if not lines:
        return "The map is empty."
    return "\n".join(lines)


def focus_labels(
    latest: dict,
    map_focus: str | None,
    focus_step_id: str | None,
) -> str | None:
    """Path of the selected node, for Voice to hold — not to dump."""
    if focus_step_id:
        lines = path_lines(_steps(latest), focus_step_id)
        if lines:
            return "\n".join(lines)
    return (map_focus or "").strip() or None


def _has(note: str, cues: tuple[str, ...]) -> bool:
    text = (note or "").lower()
    return any(cue in text for cue in cues)


def _steps(latest: dict) -> list:
    steps = ((latest.get("plan") or {}).get("progression") or {}).get("steps")
    return steps if isinstance(steps, list) else []
