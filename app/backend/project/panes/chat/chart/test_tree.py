"""Checks for talk_tree(). Run from app/:

    .venv/bin/python -m backend.project.panes.chat.chart.test_tree
"""

from backend.project.panes.chat.chart.tree import talk_tree


def main() -> None:
    assert talk_tree([]) == []
    assert talk_tree([
        {"role": "user", "text": "hello"},
        {"role": "agent", "text": "hi"},
    ]) == []

    only = [
        {"role": "user", "text": "what", "focus": "api", "focus_step_id": "p1"},
        {"role": "agent", "text": "folder", "focus": "api", "focus_step_id": "p1"},
    ]
    tree = talk_tree(only)
    assert len(tree) == 1
    assert tree[0]["label"] == "api"
    assert tree[0]["start"] == 0
    assert tree[0]["end"] == 2
    assert tree[0]["open"] is True
    assert tree[0]["focus_step_id"] == "p1"
    assert tree[0]["children"] == []

    left = only + [
        {"role": "user", "text": "ok"},
        {"role": "agent", "text": "sure"},
    ]
    closed = talk_tree(left)
    assert closed[0]["open"] is False
    assert closed[0]["end"] == 2

    grew = only + [
        {"role": "user", "text": "and this", "focus": "routes", "focus_step_id": "p2"},
        {"role": "agent", "text": "child", "focus": "routes", "focus_step_id": "p2"},
    ]
    nested = talk_tree(grew)
    assert nested[0]["label"] == "api"
    assert nested[0]["open"] is False
    assert len(nested[0]["children"]) == 1
    child = nested[0]["children"][0]
    assert child["label"] == "routes"
    assert child["start"] == 2
    assert child["end"] == 4
    assert child["open"] is True

    sibling = left + [
        {"role": "user", "text": "now", "focus": "confirm.py"},
        {"role": "agent", "text": "ok", "focus": "confirm.py"},
    ]
    roots = talk_tree(sibling)
    assert [node["label"] for node in roots] == ["api", "confirm.py"]
    assert roots[0]["children"] == []
    assert roots[1]["open"] is True
    print("OK - talk_tree")


if __name__ == "__main__":
    main()
