"""Shared label-path helpers for slash-commands (/add, /select, …)."""


def args_after_command(note: str) -> str:
    """Text after the `/command` token, or empty."""
    text = (note or "").strip()
    if not text:
        return ""
    parts = text.split(None, 1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def path_segments(args: str) -> list[str]:
    """Split `A / B / C` into labels (spaces around `/` required)."""
    return [p.strip() for p in (args or "").split(" / ") if p.strip()]


_SLASH_HINT = (
    'Put spaces around every / like: Parent / Child '
    "(not Parent /Child or Parent/Child)."
)


def slash_path_error(args: str) -> str | None:
    """If `args` uses `/` incorrectly, return an error; else None.

    Path syntax is only `Label / Label / …`. A lone `/` glued to a
    word (e.g. `CLIENT /hey`) must not become a node label.
    """
    text = (args or "").strip()
    if "/" not in text:
        return None
    if " / " not in text:
        return _SLASH_HINT
    for seg in path_segments(text):
        if "/" in seg:
            return _SLASH_HINT
    return None


def id_at_path(steps: list, labels: list[str]) -> str | None:
    """Walk label path from the forest root; first match at each level."""
    level = steps
    current_id: str | None = None
    for label in labels:
        wanted = label.strip()
        match = None
        for step in level:
            if not isinstance(step, dict):
                continue
            if (step.get("label") or "").strip() == wanted:
                match = step
                break
        if match is None:
            return None
        current_id = str(match.get("id") or "") or None
        if not current_id:
            return None
        children = match.get("children")
        level = children if isinstance(children, list) else []
    return current_id
