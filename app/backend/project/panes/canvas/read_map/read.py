"""Read an existing map back into words, on demand.

The structure is the source of truth. This module only describes what
is there. The instruction lives in model/brief/read_map.py.

Nothing here writes. Whether a reading is kept is a decision for the
caller and is deliberately not made here.
"""

import json

from backend.model.brief.read_map import READING_SCHEMA, READ_MAP_SYSTEM_PROMPT
from backend.model.client import send_message
from backend.project.panes.canvas.read_map.outline import outline_lines


def read_tree(goal_label: str, steps: list[dict]) -> dict | None:
    """{"summary"} for this tree, or None if there is nothing to read.

    `goal_label` is the project's current display text, given as
    context only. The model is told to work from the structure, and
    an untitled or throwaway name should not steer it.
    """
    lines = outline_lines(steps)
    if not lines:
        return None
    outline = "\n".join(lines)

    raw = send_message(
        READ_MAP_SYSTEM_PROMPT,
        f"Project is currently called: {goal_label}\n\nIts structure:\n{outline}",
        schema=READING_SCHEMA,
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    summary = (parsed.get("summary") or "").strip()
    if not summary:
        return None
    return {"summary": summary}
