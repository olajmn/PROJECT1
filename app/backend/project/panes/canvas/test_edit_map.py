"""The saved text of remove_map_node(), import_map_outline(),
move_map_node() and rename_map_node() - no files, no model. Run from app/:

    .venv/bin/python -m backend.project.panes.canvas.test_edit_map
"""

import backend.project.panes.canvas.edit_map as edit_map


def main() -> None:
    saved: dict = {}
    # Capture what would be saved instead of writing data/.
    edit_map.save_plan = lambda name, plan, **kw: saved.update(kw, plan=plan) or kw

    def tree() -> dict:
        return {"name": "T", "project_id": 1, "plan": {"progression": {"steps": [
            {"id": "p1", "label": "Top", "children": [
                {"id": "p2", "label": "Mid", "children": [
                    {"id": "p3", "label": "Leaf", "children": []},
                ]},
            ]},
        ]}}}

    # The text says where the node sat and what went with it, so Logs
    # and the chat's model need not guess.
    edit_map.remove_map_node(tree(), "p2")
    assert saved["feedback"] == "Removed step under Top: Mid (and 1 under it)", saved
    edit_map.remove_map_node(tree(), "p3")
    assert saved["feedback"] == "Removed step under Mid: Leaf"
    edit_map.remove_map_node(tree(), "p1")
    assert saved["feedback"] == "Removed step: Top (and 2 under it)"
    assert saved["event"] == "node_removed"

    # One import is one change, but its text counts every node it
    # brought in, not only the top level.
    forest = [{"label": "A", "children": [
        {"label": "B", "children": [{"label": "C", "children": []}]},
        {"label": "D", "children": []},
    ]}]
    edit_map.import_map_outline(tree(), forest=forest)
    assert saved["feedback"] == "Imported 4 nodes", saved
    edit_map.import_map_outline(tree(), forest=[{"label": "E", "children": []}], parent_id="p3")
    assert saved["feedback"] == "Imported 1 node under Leaf", saved

    # Moving swaps with one sibling; id and children go with it.
    def row() -> dict:
        return {"name": "T", "project_id": 1, "plan": {"progression": {"steps": [
            {"id": "p1", "label": "A", "children": []},
            {"id": "p2", "label": "B", "children": [
                {"id": "p3", "label": "B1", "children": []},
                {"id": "p4", "label": "B2", "children": []},
            ]},
        ]}}}

    def order(steps: list) -> list[str]:
        return [s["id"] for s in steps]

    edit_map.move_map_node(row(), "p2", "up")
    steps = saved["plan"]["progression"]["steps"]
    assert order(steps) == ["p2", "p1"], steps
    assert order(steps[0]["children"]) == ["p3", "p4"]
    assert saved["feedback"] == "Moved step: B above A", saved
    assert saved["event"] == "node_moved"
    edit_map.move_map_node(row(), "p3", "down")
    assert order(saved["plan"]["progression"]["steps"][1]["children"]) == ["p4", "p3"]
    assert saved["feedback"] == "Moved step under B: B1 below B2", saved
    for step_id, direction in [("p1", "up"), ("p4", "down"), ("p9", "up")]:
        try:
            edit_map.move_map_node(row(), step_id, direction)
        except ValueError:
            continue
        raise AssertionError(f"{step_id} {direction} should fail")

    # Renaming keeps the id, place, and children; the saved line carries
    # the id so the chat can show the rename in that node's conversation.
    edit_map.rename_map_node(row(), "p3", "  First  ")
    renamed = saved["plan"]["progression"]["steps"][1]
    assert renamed["children"][0] == {"id": "p3", "label": "First", "children": []}
    assert saved["feedback"] == "Renamed step: B1 → First", saved
    assert saved["event"] == "node_renamed"
    assert saved["focus_step_id"] == "p3"
    # Same name: nothing saved, the record comes back as it was.
    saved.clear()
    same = row()
    assert edit_map.rename_map_node(same, "p3", "B1") is same and not saved
    # Empty, a sibling's name, or an unknown id: refused.
    for step_id, label in [("p3", " "), ("p3", "B2"), ("p9", "X")]:
        try:
            edit_map.rename_map_node(row(), step_id, label)
        except ValueError:
            continue
        raise AssertionError(f"rename {step_id} to {label!r} should fail")
    print("OK - remove / import / move / rename map node saved text")


if __name__ == "__main__":
    main()
