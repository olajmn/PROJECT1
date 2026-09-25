"""Checks for group_events / build_status / status_text - no files, no
model. Run from app/:

    .venv/bin/python -m backend.project.status.test_status
"""

from datetime import datetime, timezone

from backend.project.status.build_status import build_status, status_text

NOW = datetime(2026, 9, 25, 20, 0, tzinfo=timezone.utc).astimezone()


def line(feedback, at, event=None, focus=None, steps=None, goal="House", **extra):
    record = {
        "project_id": 7, "goal": goal, "sim_user_id": 3, "feedback": feedback,
        "created_at": at, "plan": {"progression": {"steps": steps or []}},
    }
    if event:
        record["event"] = event
    if focus:
        record["map_focus"] = focus
    record.update(extra)
    return record


def main() -> None:
    tree = [{"label": "Rooms", "children": [{"label": "Kitchen"}, {"label": "Bath"}]}]
    history = [
        line(None, "2026-09-24T09:00:00.000+00:00", "created"),
        line("Added step: Rooms", "2026-09-24T09:01:00.000+00:00", "node_added"),
        line("Added step under Rooms: Kitchen", "2026-09-25T10:00:00.000+00:00", "node_added"),
        line("Added step under Rooms: Bath", "2026-09-25T10:01:00.000+00:00", "node_added"),
        line("Ok. Note: hi", "2026-09-25T11:00:00.000+00:00", "chat"),
        line("Ok. Note: and this?", "2026-09-25T11:01:00.000+00:00", "chat", focus="Kitchen"),
        line("Renamed: House → Home", "2026-09-25T12:00:00.000+00:00", "renamed", steps=tree, goal="Home"),
    ]
    status = build_status(history, now=NOW)

    texts = [h["text"] for h in status["history"]]
    assert texts == [
        'Renamed "House" → "Home"',
        'Chat · 2 messages about "Kitchen"',
        'Added 2 nodes under "Rooms"',
        'Added "Rooms"',
        "Created",
    ], texts
    assert [h["day"] for h in status["history"]] == ["Today", "Today", "Today", "Yesterday", "Yesterday"]
    assert status["history"][2]["nodes"] == ["Rooms"]
    assert status["earlier"] == 0

    summary = {row["label"]: row["text"] for row in status["summary"]}
    assert summary["Project"] == "Home (id#3), started 24 Sep", summary
    assert summary["Map"] == "3 nodes, 2 levels"
    assert summary["Top level"] == "Rooms"
    assert summary["Recent map work under"] == "Rooms"
    assert summary["Last talked about"] == "Kitchen"

    text = status_text(status)
    assert text.startswith("Project: Home (id#3), started 24 Sep")
    assert "History (newest first):\n  Today " in text  # the day is on every line
    assert 'Added 2 nodes under "Rooms"' in text

    # Old lines (no event, local time without offset) read the same way.
    old = build_status([
        {"project_id": 1, "goal": "Old", "feedback": None, "created_at": "2026-09-20T10:00:00"},
        {"project_id": 1, "goal": "Old", "feedback": "Imported 1 step(s)",
         "created_at": "2026-09-20T10:05:00", "plan": {}},
    ], now=NOW)
    assert [h["text"] for h in old["history"]] == ["Pasted structure (1 top node)", "Created"]
    assert build_status([]) == {"summary": [], "history": [], "earlier": 0}
    print("OK - project status")


if __name__ == "__main__":
    main()
