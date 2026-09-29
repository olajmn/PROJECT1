"""Checks for event_name() / to_event() / all_events() paging - no files,
no model. Run from app/:

    .venv/bin/python -m backend.project.test_timeline
"""

import backend.project.timeline as timeline
from backend.project.timeline import event_name, to_event


def main() -> None:
    # New lines carry `event`; it wins over the feedback text.
    assert event_name({"event": "renamed", "feedback": "Renamed: a → b"}) == "renamed"

    # Every saved line carries `event`; one without it is "other".
    assert event_name({"feedback": "Added step: roof"}) == "other"

    chat = to_event(
        {"project_id": 4, "feedback": "Sure. Note: what next?",
         "created_at": "2026-09-25T18:00:00.000+00:00", "event": "chat"},
        "House",
    )
    assert chat == {
        "at": "2026-09-25T18:00:00.000+00:00", "project_id": 4,
        "project": "House", "event": "chat", "kind": "Chat",
        "text": "what next?",
    }
    created = to_event({"project_id": 4, "feedback": None, "event": "created"}, "House")
    assert (created["kind"], created["text"]) == ("Created", "")
    renamed = to_event(
        {"project_id": 4, "feedback": "Renamed: Hus → House", "event": "renamed"},
        "House",
    )
    assert (renamed["kind"], renamed["text"]) == ("Renamed", "Renamed: Hus → House")
    long = to_event({"project_id": 4, "feedback": "Added step: " + "x" * 300}, "House")
    assert long["text"].endswith("…") and len(long["text"]) == 161

    # all_events() pages newest first: offset skips what is already shown.
    lines = [
        {"project_id": 1, "event": "node_added", "feedback": f"Added step: {n}",
         "created_at": f"2026-09-2{n}T10:00:00"}
        for n in range(1, 6)
    ]
    timeline.load_history = lambda: lines
    timeline.get_latest_for_all_projects = lambda: [{"project_id": 1, "name": "P"}]
    texts = lambda events: [e["text"] for e in events]
    assert texts(timeline.all_events(limit=2)) == ["Added step: 5", "Added step: 4"]
    assert texts(timeline.all_events(limit=2, offset=2)) == ["Added step: 3", "Added step: 2"]
    assert texts(timeline.all_events(limit=2, offset=4)) == ["Added step: 1"]
    assert timeline.all_events(limit=2, offset=9) == []
    print("OK - timeline events and paging")


if __name__ == "__main__":
    main()
