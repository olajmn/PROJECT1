"""Add folder — what a walk of one folder is allowed to see.

Not a prompt, and not Read map. No model call. `walk.py` applies
these and does nothing else: it does not read file contents, and it
does not follow symlinks. There is no depth cap.
"""

MAX_NODES = 400

# Left out entirely, in addition to any name that starts with ".".
SKIP_DIR_NAMES = frozenset({"node_modules", "__pycache__"})


def skipped(name: str) -> bool:
    """True when this name is not turned into a node."""
    return name.startswith(".") or name in SKIP_DIR_NAMES
