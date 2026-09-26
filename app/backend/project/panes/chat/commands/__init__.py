"""Talk slash-commands.

Route `/name` → a runner. Model briefs stay in `backend/model/`; this
folder only decides which command ran and returns a CommandResult.
Call sites (reply.py) save the turn and attach About-focus.

Add a command: one module + one entry in `_COMMANDS` below.
"""

from collections.abc import Callable

from backend.project.panes.chat.commands.add import run as run_add
from backend.project.panes.chat.commands.project_summary import (
    run as run_project_summary,
)
from backend.project.panes.chat.commands.result import CommandResult
from backend.project.panes.chat.commands.select import run as run_select

_Runner = Callable[..., CommandResult]

_COMMANDS: dict[str, _Runner] = {
    "/project_summary": run_project_summary,
    "/add": run_add,
    "/select": run_select,
}

_ALIASES = {
    "/project-summary": "/project_summary",
    "/map_summary": "/project_summary",
    "/map-summary": "/project_summary",
    "/read_map": "/project_summary",
    "/read-map": "/project_summary",
    "/add-node": "/add",
    "/focus": "/select",
}


def try_command(
    latest: dict,
    note: str,
    focus_step_id: str | None = None,
) -> CommandResult | None:
    """If `note` starts with a known command, run it. Otherwise None."""
    token = (note or "").strip().split(None, 1)[0].lower()
    if not token.startswith("/"):
        return None
    name = _ALIASES.get(token, token)
    runner = _COMMANDS.get(name)
    if runner is None:
        return None
    return runner(latest, note, focus_step_id=focus_step_id)
