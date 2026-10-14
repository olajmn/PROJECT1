"""thread_messages() only - no model call. Run from app/:
    .venv/bin/python -m backend.project.panes.chat.screen.test_chat_thread
"""

from backend.project.panes.chat.screen.chat_thread import thread_messages

rooms = {"progression": {"steps": [{"label": "Rooms"}]}}

# Only chat turns show: the first record, map edits, and other saved
# lines without "<reply> Note: <note>" are left to Status.
history = [
    {"name": "House", "plan": {}, "feedback": None, "event": "created"},
    {"name": "House", "plan": rooms, "feedback": "Added step: Rooms", "event": "node_added"},
    {"name": "House", "plan": rooms, "feedback": "Sure. Note: what next?", "event": "chat"},
    {"name": "House", "plan": rooms, "feedback": "Inserted tree", "event": "tree_inserted"},
]
assert thread_messages(history) == [
    {"role": "user", "text": "what next?"},
    {"role": "agent", "text": "Sure."},
]

# A turn that changed the map (/add) still shows its reply, not a
# summary of the map.
added = [
    {"name": "House", "plan": {}, "feedback": "Added Kitchen. Note: /add Kitchen", "event": "chat"},
]
assert thread_messages(added)[1] == {"role": "agent", "text": "Added Kitchen."}

# map_focus tags each turn so the UI can frame a focused stretch.
focused = thread_messages([
    {"feedback": "A room. Note: what is this?", "map_focus": "Rooms", "focus_step_id": "p1"},
    {"feedback": "Paint. Note: and now?"},
])
assert focused[0] == {
    "role": "user", "text": "what is this?", "focus": "Rooms", "focus_step_id": "p1",
}
assert focused[1]["focus"] == "Rooms"
assert "focus" not in focused[2]
assert focused[3] == {"role": "agent", "text": "Paint."}

# A turn about a day of changes carries focus_day, not a node focus.
by_day = thread_messages([{"feedback": "Two edits. Note: what changed?", "focus_day": "2026-09-27"}])
assert by_day[0] == {"role": "user", "text": "what changed?", "focus_day": "2026-09-27"}
assert by_day[1]["focus_day"] == "2026-09-27"

# `at`: the user line prefers sent_at, the agent line uses created_at.
timed = thread_messages([
    {"feedback": "Ok. Note: hi", "sent_at": "t1", "created_at": "t2"},
])
assert timed[0]["at"] == "t1" and timed[1]["at"] == "t2"

print("OK - thread_messages() shows chat turns only")
