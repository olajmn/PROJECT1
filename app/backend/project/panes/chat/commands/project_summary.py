"""/project_summary — summarise the node tree from its labels.

Packs the tree as text, sends model/brief/project_summary, returns
reply text. Does not write the tree; Talk saves the turn as usual.
"""

import json

from backend.model.brief.project_summary import (
    PROJECT_SUMMARY_SCHEMA,
    PROJECT_SUMMARY_SYSTEM_PROMPT,
)
from backend.model.client import send_message
from backend.project.node.tree_as_text import tree_lines


def run(latest: dict, note: str) -> str:
    """Reply text for `/project_summary`. `note` kept for a later args form."""
    del note  # no args yet
    steps = ((latest.get("plan") or {}).get("progression") or {}).get("steps")
    if not isinstance(steps, list) or not steps:
        return "The map is empty — nothing to summarise."
    summary = _summarise_tree(latest.get("name") or "", steps)
    if summary is None:
        return "No summary came back — try again."
    return summary


def _summarise_tree(goal_label: str, steps: list[dict]) -> str | None:
    """Model summary for this forest, or None if empty / bad response.

    `goal_label` is context only — the model works from structure.
    """
    lines = tree_lines(steps)
    if not lines:
        return None
    outline = "\n".join(lines)
    raw = send_message(
        PROJECT_SUMMARY_SYSTEM_PROMPT,
        f"Project is currently called: {goal_label}\n\nIts structure:\n{outline}",
        schema=PROJECT_SUMMARY_SCHEMA,
    )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    summary = (parsed.get("summary") or "").strip()
    return summary or None
