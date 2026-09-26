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
    assert "selected this node" in messages[0]["content"]
    assert messages[1:-1] == turns
    assert messages[-1] == {"role": "user", "content": "[about: Beds] and now?"}

    unfocused = build_messages(latest, "hi", [])
    assert len(unfocused) == 2
    assert "selected this node" not in unfocused[0]["content"]
    assert "No map node is focused" in unfocused[0]["content"]

    many = [{"feedback": f"r{i} Note: n{i}"} for i in range(MAX_TURNS + 5)]
    assert len(past_turns(many)) == 2 * MAX_TURNS
    assert past_turns(many)[-1]["content"] == f"r{MAX_TURNS + 4}"
    print("OK - build_messages / past_turns")


if __name__ == "__main__":
    main()
