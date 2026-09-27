"""Saved trees — a node's subtree kept as bare structure (labels,
order, children; no ids) in a per-account library, and inserted later
under any node as new nodes with fresh ids.

Above panes, like project/node/: canvas's ⋯ menu is only one face.
What is copied (structure, never ids): structure_of() in project/node/,
described in project/node/README.md. Decision: docs/05-decisions.md #54.

Files:
  saved_trees.py — save from a node, list, insert, delete
"""

from backend.project.saved_trees.saved_trees import (
    insert_saved_tree,
    remove_saved_tree,
    save_tree_from_node,
    saved_trees_for,
)

__all__ = [
    "insert_saved_tree",
    "remove_saved_tree",
    "save_tree_from_node",
    "saved_trees_for",
]
