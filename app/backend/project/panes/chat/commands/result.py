"""Command result: reply text, optional saved record, optional UI select
or map display toggle."""

from typing import NamedTuple


class CommandResult(NamedTuple):
    reply: str
    record: dict | None = None
    """If set, command already saved (e.g. /add wrote a node)."""
    select_id: str | None = None
    select_label: str | None = None
    """If set, browser should select this node (e.g. /select)."""
    toggle_map_ids: bool = False
    """If set, browser switches the map between ids and labels (/id)."""
