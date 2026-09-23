"""Checks for format_hold(). Run from app/:

    .venv/bin/python -m backend.project.panes.chat.test_hold
"""

from backend.project.panes.chat.hold import MAX_CHARS, format_hold, scope_hold


def main() -> None:
    assert format_hold([]) is None
    block = format_hold([
        {"role": "user", "text": "hello"},
        {"role": "agent", "text": "Hi there."},
    ])
    assert block is not None
    assert "User: hello" in block
    assert "Agent: Hi there." in block
    long = "x" * (MAX_CHARS + 50)
    cut = format_hold([{"role": "agent", "text": long}])
    assert cut is not None
    assert "…" in cut
    assert str(MAX_CHARS + 50) not in cut
    mixed = [
        {"role": "user", "text": "hello"},
        {"role": "user", "text": "what is this", "focus": "current_time.py", "focus_step_id": "p1"},
        {"role": "agent", "text": "a clock file", "focus": "current_time.py", "focus_step_id": "p1"},
        {"role": "user", "text": "and this", "focus": "foundation", "focus_step_id": "p2"},
    ]
    assert [m["text"] for m in scope_hold(mixed, None, None)] == ["hello"]
    assert [m["text"] for m in scope_hold(mixed, "foundation", "p2")] == ["and this"]
    assert [m["text"] for m in scope_hold(mixed, "current_time.py", "p1")] == [
        "what is this",
        "a clock file",
    ]
    print("OK - format_hold")


if __name__ == "__main__":
    main()
