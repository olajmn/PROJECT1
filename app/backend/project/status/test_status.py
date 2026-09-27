"""Checks for build_status / status_text day-change pulse - no files, no
model. Run from app/:

    .venv/bin/python -m backend.project.status.test_status
"""

from datetime import datetime, timezone

from backend.project.status.build_status import (
    build_status,
    recent_changes_text,
    status_text,
)

NOW = datetime(2026, 9, 25, 20, 0, tzinfo=timezone.utc).astimezone()


def line(feedback, at, event=None, focus=None, steps=None, name="House", **extra):
    record = {
        "project_id": 7, "name": name, "account_id": 3, "feedback": feedback,
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
        line("Renamed: House → Home", "2026-09-25T12:00:00.000+00:00", "renamed", steps=tree, name="Home"),
    ]
    status = build_status(history, now=NOW)

    # Chat excluded; Sep 24: created + node_added = 2; Sep 25: 2 adds + rename = 3.
    assert [(h["day"], h["changes"], h["text"]) for h in status["history"]] == [
        ("Today", 3, "3 changes"),
        ("Yesterday", 2, "2 changes"),
    ], status["history"]
    assert status["earlier"] == 0

    summary = {row["label"]: row["text"] for row in status["summary"]}
    assert summary["Project"] == "Home, started 24 Sep", summary
    assert summary["Map"] == "3 nodes, 2 levels"
    assert "Top level" not in summary
    assert "Recent map work under" not in summary
    assert "Last talked about" not in summary
    assert "Last change" in summary
    assert list(summary) == ["Project", "Last change", "Map"], list(summary)

    text = status_text(status)
    assert text.startswith("Project: Home, started 24 Sep")
    assert "Last change:" in text
    assert "changes" not in text  # the day pulse is for the panel only

    # Quiet days between first change and now are listed as 0.
    gap = build_status([
        line(None, "2026-09-20T10:00:00.000+00:00", "created"),
        line("Added step: A", "2026-09-20T10:05:00.000+00:00", "node_added"),
    ], now=NOW)
    days = [(h["day"], h["changes"]) for h in gap["history"]]
    assert days[0] == ("Today", 0), days
    assert days[-1] == ("20 Sep", 2), days
    assert sum(1 for _, n in days if n == 0) >= 1

    # Older timestamps (local time, no offset) still count; chat excluded.
    old = build_status([
        {"project_id": 1, "name": "Old", "feedback": None, "event": "created",
         "created_at": "2026-09-20T10:00:00"},
        {"project_id": 1, "name": "Old", "feedback": "Imported 1 step(s)",
         "event": "pasted", "created_at": "2026-09-20T10:05:00", "plan": {}},
        {"project_id": 1, "name": "Old", "feedback": "Hello Note: hi",
         "event": "chat", "created_at": "2026-09-20T11:00:00"},
    ], now=NOW)
    assert old["history"][-1]["changes"] == 2, old["history"]

    assert build_status([]) == {"summary": [], "history": [], "earlier": 0}

    # Recent changes: what each one was, newest first, chat left out.
    tape = [
        {"feedback": None, "event": "created", "created_at": "2026-09-20T10:00:00"},
        {"feedback": "Imported 1 step(s)", "event": "pasted", "created_at": "2026-09-20T10:05:00"},
        {"feedback": "Hello Note: hi", "event": "chat", "created_at": "2026-09-20T11:00:00"},
        {"feedback": "Renamed: A → B", "event": "renamed", "created_at": "2026-09-20T12:00:00"},
    ]
    recent = recent_changes_text(tape, now=NOW).splitlines()
    assert recent[0] == "Recent changes (newest first):"
    assert recent[1].endswith("— Renamed: A → B"), recent
    assert recent[2].endswith("— Imported 1 step(s)")
    assert recent[3].endswith("— Created")
    assert len(recent) == 4
    assert len(recent_changes_text(tape, now=NOW, limit=1).splitlines()) == 2
    assert recent_changes_text(tape[2:3], now=NOW) == ""
    print("OK - project status day pulse / recent changes")


if __name__ == "__main__":
    main()
