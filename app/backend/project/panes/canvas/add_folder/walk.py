"""Walk one folder into a tree of entities.

Each folder and each file is one node: label is the name, path is the
absolute path, children are what that folder contains. The chosen
folder is the root node, not a flat list of its contents.

What gets left out, and when the walk stops, is `rules.py`.
"""

from pathlib import Path

from backend.project.panes.canvas.add_folder.rules import MAX_NODES, skipped


def folder_tree(folder: str) -> list[dict]:
    """One-item forest: the folder itself, with its contents nested."""
    text = (folder or "").strip()
    if not text:
        raise ValueError("folder path is empty")
    root = Path(text).expanduser().resolve()
    if not root.exists():
        raise ValueError("folder not found")
    if not root.is_dir():
        raise ValueError("that path is a file, not a folder")

    count = {"n": 0}
    return [_node(root, count)]


def _node(path: Path, count: dict) -> dict:
    count["n"] += 1
    if count["n"] > MAX_NODES:
        raise ValueError("folder is too large to map in one pass")

    children: list[dict] = []
    if path.is_dir(follow_symlinks=False):
        children = [_node(entry, count) for entry in _entries(path)]

    return {
        "label": path.name,
        "path": str(path),
        "children": children,
    }


def _entries(path: Path) -> list[Path]:
    try:
        names = list(path.iterdir())
    except OSError as e:
        raise ValueError(f"cannot read {path.name}: {e.strerror}") from e
    kept = [
        entry
        for entry in names
        if not skipped(entry.name)
    ]
    kept.sort(key=lambda entry: (not entry.is_dir(follow_symlinks=False), entry.name.casefold()))
    return kept
