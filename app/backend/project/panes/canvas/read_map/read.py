"""Read an existing map back into words, on demand.

The structure is the source of truth. This module only describes what
is there. The instruction lives in `prompt.py`.

Nothing here writes. Whether a reading is kept is a decision for the
caller and is deliberately not made here.
"""

import json

from backend.llm_client import send_message
from backend.project.panes.canvas.read_map.prompt import READ_MAP_SYSTEM_PROMPT

READING_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
    },
    "required": ["summary"],
}

# A tree far past this is cheaper to truncate than to fail on, and the
# shape is legible from the first levels anyway. A ceiling, not a target.
MAX_LINES = 400


def read_tree(goal_label: str, steps: list[dict]) -> dict | None:
    """{"summary"} for this tree, or None if there is nothing to read.

    `goal_label` is the project's current display text, given as
    context only. The model is told to work from the structure, and
    an untitled or throwaway name should not steer it.
    """
    lines: list[str] = []
    _outline(steps, 0, lines)
    if not lines:
        return None
    outline = "\n".join(lines[:MAX_LINES])

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


def _outline(steps: list[dict], depth: int, lines: list[str]) -> None:
    """Collect the tree as indented lines — the same shape
    text_to_tree.py parses, so what the model reads is what a person
    would paste."""
    for step in steps:
        if not isinstance(step, dict):
            continue
        label = (step.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
        children = step.get("children")
        if isinstance(children, list):
            _outline(children, depth + 1, lines)
