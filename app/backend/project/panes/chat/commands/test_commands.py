"""Checks for slash-command dispatch — no model call. Run from app/:

    .venv/bin/python -m backend.project.panes.chat.commands.test_commands
"""

from backend.project.panes.chat.commands import try_command
from backend.project.panes.chat.commands import add as add_mod


def main() -> None:
    empty = {
        "name": "Empty",
        "project_id": 1,
        "plan": {"progression": {"steps": []}},
    }
    assert try_command(empty, "hello") is None
    assert try_command(empty, "") is None
    # Unknown or mistyped commands answer without the model.
    unknown = try_command(empty, "/id¨")
    assert unknown is not None and unknown.record is None
    assert unknown.reply.startswith("Unknown command /id¨.")
    assert not unknown.toggle_map_ids
    msg = "The map is empty — nothing to summarise."
    assert try_command(empty, "/project_summary").reply == msg
    assert try_command(empty, "/map_summary").reply == msg
    assert try_command(empty, "/read_map").reply == msg

    # /add parse — no save (missing focus / parent).
    result = try_command(empty, "/add")
    assert result is not None and result.record is None
    assert "Usage" in result.reply

    result = try_command(empty, "/add alone")
    assert result is not None and result.record is None
    assert "Usage" in result.reply

    result = try_command(empty, "/add Missing / Child")
    assert result is not None and result.record is None
    assert "No node at path" in result.reply

    tree = {
        "name": "T",
        "project_id": 99,
        "plan": {
            "progression": {
                "steps": [
                    {
                        "id": "p1",
                        "label": "CLIENT",
                        "children": [
                            {
                                "id": "p2",
                                "label": "hey3",
                                "children": [],
                            },
                        ],
                    }
                ]
            }
        },
    }
    parent_id, child, err = add_mod._resolve(tree, "client", "p1")
    assert err is None and parent_id == "p1" and child == "client"
    parent_id, child, err = add_mod._resolve(tree, "CLIENT / bills", None)
    assert err is None and parent_id == "p1" and child == "bills"
    parent_id, child, err = add_mod._resolve(tree, "CLIENT / hey3 / hey", None)
    assert err is None and parent_id == "p2" and child == "hey"
    parent_id, child, err = add_mod._resolve(tree, "CLIENT / missing / hey", None)
    assert parent_id is None and "No node at path" in (err or "")

    # Malformed path must not mint a label that contains "/".
    bad = try_command(tree, "/add CLIENT /hey")
    assert bad is not None and bad.record is None
    assert "spaces around" in bad.reply.lower()
    bad = try_command(tree, "/add client /add hey /hey")
    assert bad is not None and bad.record is None
    assert "spaces around" in bad.reply.lower()
    bad = try_command(tree, "/select CLIENT /hey")
    assert bad is not None and bad.select_id is None
    assert "spaces around" in bad.reply.lower()

    selected = try_command(tree, "/select CLIENT / hey3")
    assert selected is not None
    assert selected.select_id == "p2"
    assert selected.select_label == "hey3"
    assert "Selected:" in selected.reply
    assert try_command(tree, "/focus CLIENT").select_id == "p1"

    # /id: with a node selected, its id and path; without, a map toggle.
    shown = try_command(tree, "/id", focus_step_id="p2")
    assert shown.reply == "hey3 → p2 (CLIENT / hey3)", shown.reply
    assert not shown.toggle_map_ids and shown.record is None
    toggled = try_command(tree, "/id")
    assert toggled.toggle_map_ids and toggled.record is None

    # A clashing sibling label is numbered, not refused (decision #53).
    import backend.project.panes.canvas.edit_map as edit_map
    real_save = edit_map.save_plan
    edit_map.save_plan = lambda name, plan, **kw: {"name": name, "plan": plan, **kw}
    try:
        dup = try_command(tree, "/add CLIENT / hey3")
    finally:
        edit_map.save_plan = real_save
    assert dup is not None and dup.record is not None
    assert dup.reply.endswith(": hey3 (2)."), dup.reply

    print("OK - try_command dispatch")


if __name__ == "__main__":
    main()
