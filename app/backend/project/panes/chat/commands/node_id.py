"""/id — show node identity behind the labels.

With a node selected: reply with that node's id and label path.
Without one: tell the browser to switch the whole map between showing
ids and labels (a display toggle only; nothing about the tree changes,
and the tree is not dumped into the thread — docs/05-decisions.md #48).
No model.
"""

from backend.project.node.tree_as_text import find_path
from backend.project.panes.chat.commands.node_path import steps_of
from backend.project.panes.chat.commands.result import CommandResult

_TOGGLED = (
    "Map switched between node ids and names. Type /id again to switch back."
)


def run(
    latest: dict,
    note: str,
    focus_step_id: str | None = None,
) -> CommandResult:
    del note  # /id takes no arguments
    if not focus_step_id:
        return CommandResult(_TOGGLED, toggle_map_ids=True)
    path = find_path(steps_of(latest), focus_step_id)
    if path is None:
        return CommandResult(f"No node with id {focus_step_id}.")
    labels = " / ".join((step.get("label") or "").strip() for step in path)
    node = path[-1]
    return CommandResult(f"{node.get('label')} → {node.get('id')} ({labels})")
