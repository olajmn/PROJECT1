"""remove_map_node()'s saved text - no files, no model. Run from app/:

    .venv/bin/python -m backend.project.panes.canvas.test_edit_map
"""

import backend.project.panes.canvas.edit_map as edit_map


def main() -> None:
    saved: dict = {}
    # Capture what would be saved instead of writing data/.
    edit_map.save_plan = lambda name, plan, **kw: saved.update(kw) or kw

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
    print("OK - remove_map_node saved text")


if __name__ == "__main__":
    main()
