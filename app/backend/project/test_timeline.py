"""Checks for event_name() / to_event() - no files, no model. Run from app/:

    .venv/bin/python -m backend.project.test_timeline
"""

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
    print("OK - timeline events")


if __name__ == "__main__":
    main()
