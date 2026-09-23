"""Walk one folder into a tree of entities.

Each folder and each file is one node: label is the name, path is the
absolute path, children are what that folder contains. The chosen
folder is the root node, not a flat list of its contents.

Hidden names, node_modules, and __pycache__ are skipped. Symlinks are
listed and not followed. There is no depth cap. The node count is
capped so one click cannot map the whole disk.
"""

from pathlib import Path

MAX_NODES = 400
SKIP_DIR_NAMES = {"node_modules", "__pycache__"}


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
        if not entry.name.startswith(".") and entry.name not in SKIP_DIR_NAMES
    ]
    kept.sort(key=lambda entry: (not entry.is_dir(follow_symlinks=False), entry.name.casefold()))
    return kept
