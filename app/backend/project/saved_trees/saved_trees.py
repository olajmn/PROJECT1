"""Save a node's subtree as structure, list an account's saved trees,
insert one under a node, delete one. No model call.

Storage is backend/storage/saved_trees_persistence.py; inserting goes
through edit_map.import_map_outline(), the same path as Paste, so
fresh ids and sibling-label numbering come from there.
"""

from backend.project.node import find_step, steps_of, structure_of
from backend.project.panes.canvas.edit_map import import_map_outline
from backend.storage.saved_trees_persistence import (
    add_saved_tree,
    delete_saved_tree,
    get_saved_tree,
    load_saved_trees,
)


def save_tree_from_node(latest: dict, step_id: str) -> dict:
    """Store `step_id` and everything under it in the project's account
    library, named after the node. Saving the same node twice makes two
    saved trees: each is a snapshot, not a link."""
    step = find_step(steps_of(latest), step_id)
    if step is None:
        raise ValueError(f"step not found: {step_id}")
    tree = structure_of(step)
    return add_saved_tree(
        tree["label"],
        tree,
        latest.get("sim_user_id"),
        source={"project_id": latest["project_id"], "step_id": step_id},
    )


def saved_trees_for(latest: dict) -> list[dict]:
    """The saved trees of this project's account, newest first."""
    account = latest.get("sim_user_id")
    mine = [t for t in load_saved_trees() if t.get("sim_user_id") == account]
    return list(reversed(mine))


def insert_saved_tree(latest: dict, tree_id: str, parent_id: str | None) -> dict:
    """Insert a saved tree under `parent_id` (or at the top level) as new
    nodes and return the saved project record. Only the project's own
    account library can be used."""
    saved = get_saved_tree(tree_id)
    if saved is None or saved.get("sim_user_id") != latest.get("sim_user_id"):
        raise ValueError(f"saved tree not found: {tree_id}")
    return import_map_outline(
        latest,
        parent_id=parent_id,
        forest=[saved["tree"]],
        event="tree_inserted",
    )


def remove_saved_tree(tree_id: str) -> dict:
    removed = delete_saved_tree(tree_id)
    if removed is None:
        raise ValueError(f"saved tree not found: {tree_id}")
    return removed
