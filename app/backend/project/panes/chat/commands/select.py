"""/select — focus a node by label path (same path spelling as /add).

No model. Does not change the tree. Reply stamps About-focus; the
browser also selects the node from the chat response.
"""

from backend.project.node import find_step, steps_of
from backend.project.panes.chat.commands.node_path import (
    args_after_command,
    id_at_path,
    path_segments,
    slash_path_error,
)
from backend.project.panes.chat.commands.result import CommandResult

_USAGE = "Usage: /select Node, or /select Parent / Child / …"


def run(
    latest: dict,
    note: str,
    focus_step_id: str | None = None,
) -> CommandResult:
    del focus_step_id  # path is explicit
    args = args_after_command(note)
    if not args:
        return CommandResult(_USAGE)
    bad = slash_path_error(args)
    if bad:
        return CommandResult(bad)
    segments = path_segments(args)
    if not segments:
        return CommandResult(_USAGE)
    step_id = id_at_path(steps_of(latest), segments)
    if step_id is None:
        return CommandResult(f'No node at path "{" / ".join(segments)}".')
    step = find_step(steps_of(latest), step_id) or {}
    label = (step.get("label") or segments[-1]).strip() or segments[-1]
    shown = " / ".join(segments)
    return CommandResult(
        reply=f"Selected: {shown}.",
        select_id=step_id,
        select_label=label,
    )
