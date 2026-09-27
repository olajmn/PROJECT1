"""Checks for saved trees — no model call, no writes to data/. Run from app/:

    .venv/bin/python -m backend.project.saved_trees.test_saved_trees
"""

import tempfile
from pathlib import Path

import backend.project.panes.canvas.edit_map as edit_map
import backend.storage.saved_trees_persistence as store
from backend.project.saved_trees import (
    insert_saved_tree,
    remove_saved_tree,
    save_tree_from_node,
    saved_trees_for,
)


def _project(project_id: int, account: int | None, steps: list) -> dict:
    return {
        "name": "P",
        "project_id": project_id,
        "account_id": account,
        "plan": {"progression": {"steps": steps}},
    }


def main() -> None:
    real_file, real_save = store.SAVED_TREES_FILE, edit_map.save_plan
    with tempfile.TemporaryDirectory() as tmp:
        store.SAVED_TREES_FILE = Path(tmp) / "saved_trees.json"
        edit_map.save_plan = lambda name, plan, **kw: {"name": name, "plan": plan, **kw}
        try:
            _check()
        finally:
            store.SAVED_TREES_FILE, edit_map.save_plan = real_file, real_save
    print("OK - saved trees")


def _check() -> None:
    recipe = {
        "id": "p1", "label": "Pasta Bolognese", "resolved": True, "ordered": False,
        "children": [
            {"id": "p2", "label": "Ingredients", "path": "/tmp/x", "children": [
                {"id": "p3", "label": "Pasta", "children": []},
            ]},
            {"id": "p4", "label": "Method", "children": []},
        ],
    }
    source = _project(1, 7, [recipe])

    # Saved as structure: no id, resolved, or path anywhere.
    saved = save_tree_from_node(source, "p1")
    assert saved["id"] == "t1" and saved["name"] == "Pasta Bolognese"
    assert saved["source"] == {"project_id": 1, "step_id": "p1"}
    tree = saved["tree"]
    assert tree["ordered"] is False
    flat = repr(tree)
    assert "'id'" not in flat and "resolved" not in flat and "path" not in flat

    # Library is per account.
    assert [t["id"] for t in saved_trees_for(source)] == ["t1"]
    assert saved_trees_for(_project(2, 8, [])) == []

    # Insert under a node that already has the same label: fresh ids,
    # numbered top label, `ordered` kept.
    target = _project(3, 7, [{"id": "p5", "label": "Recipes", "children": [
        {"id": "p6", "label": "Pasta Bolognese", "children": []},
    ]}])
    record = insert_saved_tree(target, "t1", "p5")
    recipes = record["plan"]["progression"]["steps"][0]["children"]
    inserted = recipes[-1]
    assert inserted["label"] == "Pasta Bolognese (2)"
    assert inserted["ordered"] is False and inserted["resolved"] is False
    ids = [inserted["id"], *(c["id"] for c in inserted["children"])]
    assert "p1" not in ids and "p2" not in ids and len(set(ids)) == len(ids)
    assert [c["label"] for c in inserted["children"]] == ["Ingredients", "Method"]

    # Top level (no parent) works too.
    top = insert_saved_tree(target, "t1", None)
    assert top["plan"]["progression"]["steps"][-1]["label"] == "Pasta Bolognese"

    # Another account's tree can't be inserted.
    try:
        insert_saved_tree(_project(4, 8, []), "t1", None)
        raise AssertionError("inserted another account's tree")
    except ValueError:
        pass

    # Delete retires the id.
    remove_saved_tree("t1")
    assert saved_trees_for(source) == []
    assert save_tree_from_node(source, "p1")["id"] == "t2"


if __name__ == "__main__":
    main()
