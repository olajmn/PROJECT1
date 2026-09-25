"""Checks for event_name() / to_event() - no files, no model. Run from app/:

    .venv/bin/python -m backend.project.test_timeline
"""

from backend.project.timeline import event_name, to_event


def main() -> None:
    # New lines carry `event`; it wins over the feedback text.
    assert event_name({"event": "renamed", "feedback": "Renamed: a → b"}) == "renamed"

    # Older lines are named from their feedback text.
    old = {
        None: "created",
        "Hi there. Note: hello": "chat",
        "Cancelled": "archived",
        "Added step: roof": "node_added",
        "Added step under Roof: tiles": "node_added",
        "Imported 3 step(s)": "pasted",
        "Removed step: roof": "node_removed",
        "Zoomed into: roof": "suggested",
        "Moved to Vision: id#2": "owner_changed",
        "suggest three rooms": "chat_added_nodes",
    }
    for feedback, want in old.items():
        assert event_name({"feedback": feedback}) == want, (feedback, want)

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
    created = to_event({"project_id": 4, "feedback": None}, "House")
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
