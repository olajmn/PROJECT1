"""Checks for slash-command dispatch — no model call. Run from app/:

    .venv/bin/python -m backend.project.panes.chat.commands.test_commands
"""

from backend.project.panes.chat.commands import try_command


def main() -> None:
    empty = {"name": "Empty", "plan": {"progression": {"steps": []}}}
    assert try_command(empty, "hello") is None
    assert try_command(empty, "/unknown") is None
    msg = "The map is empty — nothing to summarise."
    assert try_command(empty, "/project_summary") == msg
    assert try_command(empty, "/map_summary") == msg
    assert try_command(empty, "/read_map") == msg
    print("OK - try_command dispatch")


if __name__ == "__main__":
    main()
