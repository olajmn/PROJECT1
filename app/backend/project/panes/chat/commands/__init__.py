"""Talk slash-commands.

Route `/name` → a runner. Model briefs stay in `backend/model/`; this
folder only decides which command ran and returns reply text.
Call sites (reply.py) still save and stamp the turn.

Add a command: one module + one entry in `_COMMANDS` below.
"""

from backend.project.panes.chat.commands.project_summary import run as run_project_summary

# Canonical name → runner(latest, note) -> reply text.
_COMMANDS = {
    "/project_summary": run_project_summary,
}

# Typed variants map to a canonical name.
_ALIASES = {
    "/project-summary": "/project_summary",
    "/map_summary": "/project_summary",
    "/map-summary": "/project_summary",
    "/read_map": "/project_summary",
    "/read-map": "/project_summary",
}


def try_command(latest: dict, note: str) -> str | None:
    """If `note` starts with a known command, run it and return the
    reply text. Otherwise None — ordinary Talk continues."""
    token = (note or "").strip().split(None, 1)[0].lower()
    if not token.startswith("/"):
        return None
    name = _ALIASES.get(token, token)
    runner = _COMMANDS.get(name)
    if runner is None:
        return None
    return runner(latest, note)
