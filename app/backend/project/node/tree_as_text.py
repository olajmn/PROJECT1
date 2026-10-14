"""Tree as text — indented labels and paths. No model.

For the program and the LLM (the chat brief), not a
human Print feature. Same shape text_to_tree.py parses so every
consumer looks at the same tree.
"""

MAX_LINES = 400


def tree_lines(steps: list) -> list[str]:
    """Indented labels from this forest, capped at MAX_LINES."""
    lines: list[str] = []
    _collect(steps, 0, lines)
    return lines[:MAX_LINES]


def tree_of(step: dict) -> list[str]:
    """One node and what sits under it."""
    return tree_lines([step])


def find_path(steps: list, step_id: str) -> list[dict] | None:
    """Root-to-node list of step dicts, or None."""
    wanted = (step_id or "").strip()
    if not wanted:
        return None
    for step in steps:
        if not isinstance(step, dict):
            continue
        if str(step.get("id") or "") == wanted:
            return [step]
        children = step.get("children")
        if isinstance(children, list):
            rest = find_path(children, wanted)
            if rest is not None:
                return [step, *rest]
    return None


def path_lines(steps: list, step_id: str) -> list[str]:
    """Ancestors, this node, and its children — indented labels."""
    path = find_path(steps, step_id)
    if path is None:
        return []
    lines: list[str] = []
    for depth, step in enumerate(path[:-1]):
        label = (step.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
    last = path[-1]
    last_depth = max(len(path) - 1, 0)
    for line in tree_of(last):
        # tree_of starts at depth 0; shift to sit under ancestors.
        raw = line.lstrip()
        extra = (len(line) - len(raw)) // 2
        lines.append(f"{'  ' * (last_depth + extra)}{raw}")
    return lines[:MAX_LINES]


def find_step(steps: list, step_id: str) -> dict | None:
    """The step dict with this id, or None."""
    wanted = (step_id or "").strip()
    if not wanted:
        return None
    for step in steps:
        if not isinstance(step, dict):
            continue
        if str(step.get("id") or "") == wanted:
            return step
        children = step.get("children")
        if isinstance(children, list):
            found = find_step(children, wanted)
            if found is not None:
                return found
    return None


def _collect(steps: list, depth: int, lines: list[str]) -> None:
    for step in steps:
        if not isinstance(step, dict):
            continue
        label = (step.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
        children = step.get("children")
        if isinstance(children, list):
            _collect(children, depth + 1, lines)
