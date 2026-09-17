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
assert "8 weeks" in messages[2]["text"]
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
print("OK - thread_messages() builds You/Agent lines from history")
