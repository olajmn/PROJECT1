"""Command result: reply text, optional saved record, optional UI select."""

from typing import NamedTuple


class CommandResult(NamedTuple):
    reply: str
    record: dict | None = None
    """If set, command already saved (e.g. /add wrote a node)."""
    select_id: str | None = None
    select_label: str | None = None
    """If set, browser should select this node (e.g. /select)."""
