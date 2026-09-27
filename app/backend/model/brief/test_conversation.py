"""Checks for build_messages() / past_turns() - no model call. Run from app/:

    .venv/bin/python -m backend.model.brief.test_conversation
"""

from backend.model.brief.conversation import (
    MAX_TURNS,
    build_messages,
    past_turns,
)


def main() -> None:
    latest = {
        "name": "Garden",
        "plan": {"progression": {"steps": [
            {"id": "p1", "label": "Beds", "children": []},
        ]}},
    }
    history = [
        {"feedback": None},  # first record: no turn
        {"feedback": "Zoomed into: Beds"},  # map edit: no turn
        {"feedback": "Sounds good. Note: hello"},
        {"feedback": "Beds hold soil. Note: what is this", "map_focus": "Beds"},
    ]

    turns = past_turns(history)
    assert turns == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Sounds good."},
        {"role": "user", "content": "[about: Beds] what is this"},
        {"role": "assistant", "content": "Beds hold soil."},
    ]

    messages = build_messages(latest, "and now?", history, "Beds", "p1")
    assert messages[0]["role"] == "system"
    assert '"Garden"' in messages[0]["content"]
    assert "Beds" in messages[0]["content"]
    assert "has selected this part" in messages[0]["content"]
    assert messages[1:-1] == turns
    assert messages[-1] == {"role": "user", "content": "[about: Beds] and now?"}

    unfocused = build_messages(latest, "hi", [])
    assert len(unfocused) == 2
    assert "has selected this part" not in unfocused[0]["content"]
    assert "Nothing is selected" in unfocused[0]["content"]

    many = [{"feedback": f"r{i} Note: n{i}"} for i in range(MAX_TURNS + 5)]
    assert len(past_turns(many)) == 2 * MAX_TURNS
    assert past_turns(many)[-1]["content"] == f"r{MAX_TURNS + 4}"
    # Map text and the selected node's path, as the system text shows them.
    tree = {
        "plan": {"progression": {"steps": [
            {"id": "p1", "label": "Sample", "children": [
                {"id": "p2", "label": "src", "children": [
                    {"id": "p4", "label": "main.py", "children": []},
                ]},
                {"id": "p3", "label": "readme.txt", "children": []},
            ]},
        ]}},
    }
    system = build_messages(tree, "hi", [], "main.py", "p4")[0]["content"]
    assert "readme.txt" in system
    assert "what it contains):\nSample\n  src\n    main.py" in system
    loose = build_messages(tree, "hi", [], "loose", None)[0]["content"]
    assert "what it contains):\nloose" in loose
    empty = build_messages({"plan": {}}, "hi", [])[0]["content"]
    assert "The project has no parts yet." in empty
    print("OK - build_messages / past_turns / background")


if __name__ == "__main__":
    main()
