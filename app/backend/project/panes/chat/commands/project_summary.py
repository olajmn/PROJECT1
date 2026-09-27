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
from backend.project.node import steps_of, tree_lines
from backend.project.panes.chat.commands.result import CommandResult


def run(
    latest: dict,
    note: str,
    focus_step_id: str | None = None,
) -> CommandResult:
    """Talk saves the turn as usual."""
    del note, focus_step_id  # no args / focus yet
    steps = steps_of(latest)
    if not steps:
        return CommandResult("The map is empty — nothing to summarise.")
    summary = _summarise_tree(latest.get("name") or "", steps)
    if summary is None:
        return CommandResult("No summary came back — try again.")
    return CommandResult(summary)


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
