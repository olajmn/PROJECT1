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
    # A selected day of changes: listed in the background, tagged on turns.
    tape = [
        {"feedback": "Added step: Beds", "event": "node_added", "created_at": "2026-09-20T12:00:00"},
        {"feedback": "Two beds. Note: what changed?", "event": "chat",
         "created_at": "2026-09-20T13:00:00", "focus_day": "2026-09-20"},
    ]
    day = build_messages(latest, "and?", tape, focus_day="2026-09-20")
    assert "selected the changes on 20 Sep" in day[0]["content"]
    assert "Added step: Beds" in day[0]["content"]
    assert "Nothing is selected" not in day[0]["content"]
    assert day[1]["content"] == "[about: changes on 20 Sep] what changed?"
    assert day[-1]["content"] == "[about: changes on 20 Sep] and?"
    # After a rename, past turns name the node as it is called now, and
    # what it was called then.
    renamed_tree = {"name": "Garden", "plan": {"progression": {"steps": [
        {"id": "p1", "label": "Flower beds", "children": []},
    ]}}}
    talk = [{"feedback": "Beds hold soil. Note: what is this",
             "map_focus": "Beds", "focus_step_id": "p1"}]
    later = build_messages(renamed_tree, "and now?", talk)
    assert later[1] == {"role": "user",
                        "content": "[about: Flower beds (then called Beds)] what is this"}
    assert past_turns(talk, {"p1": "Beds"})[0]["content"] == "[about: Beds] what is this"

    print("OK - build_messages / past_turns / background / selected day / renamed node")


if __name__ == "__main__":
    main()
