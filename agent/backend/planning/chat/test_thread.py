"""thread_messages() only - no model call. Run from agent/:
    .venv/bin/python -m backend.planning.chat.test_thread
"""

from backend.planning.chat.thread import thread_messages

history = [
    {
        "goal": "start working out",
        "plan": {"clarification": "How often can you train?"},
        "feedback": None,
    },
    {
        "goal": "start working out",
        "plan": {"suggested_duration": "8 weeks"},
        "feedback": "I weigh 90 kilograms.",
    },
]

messages = thread_messages(history)
assert messages[0] == {"role": "agent", "text": "How often can you train?"}
assert messages[1] == {"role": "user", "text": "I weigh 90 kilograms."}
assert messages[2]["role"] == "agent"
assert "timeframe" in messages[2]["text"].lower() or "deadline" in messages[2]["text"].lower()
assert len(messages) == 3

# A check-in stores "Still working on it. Note: <raw>" and repeats the
# previous surface - the thread should show the raw note and the ack,
# not the labeled blob and not the same next-action twice.
check_in = history + [
    {
        "goal": "start working out",
        "plan": {"suggested_duration": "8 weeks"},
        "feedback": "Still working on it. Note: still working",
    },
]
checked = thread_messages(check_in)
assert checked[3] == {"role": "user", "text": "still working"}
assert checked[4] == {"role": "agent", "text": "Still working on it."}

# map_focus tags each turn so the UI can frame a focused stretch.
focused = [
    {
        "goal": "becoming a developer",
        "plan": {"now": "hello"},
        "feedback": None,
    },
    {
        "goal": "becoming a developer",
        "plan": {"now": "hello"},
        "feedback": "what is this?",
        "map_focus": "concept 4",
        "focus_step_id": "p2",
    },
    {
        "goal": "becoming a developer",
        "plan": {"now": "hello"},
        "feedback": "make 3 ideas",
        "map_focus": "concept 4",
        "focus_step_id": "p2",
    },
    {
        "goal": "becoming a developer",
        "plan": {"now": "hello"},
        "feedback": "and now?",
    },
]
focused_msgs = thread_messages(focused)
assert focused_msgs[1] == {
    "role": "user",
    "text": "what is this?",
    "focus": "concept 4",
    "focus_step_id": "p2",
}
assert focused_msgs[2]["focus_step_id"] == "p2"
assert focused_msgs[3]["focus"] == "concept 4"
assert focused_msgs[4]["focus"] == "concept 4"
assert "focus" not in focused_msgs[5]  # general again
assert focused_msgs[5] == {"role": "user", "text": "and now?"}
print("OK - thread_messages() builds You/Agent lines from history")
