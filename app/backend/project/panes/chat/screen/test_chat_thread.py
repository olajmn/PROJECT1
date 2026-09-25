"""thread_messages() only - no model call. Run from app/:
    .venv/bin/python -m backend.project.panes.chat.screen.test_chat_thread
"""

from backend.project.panes.chat.screen.chat_thread import thread_messages

empty = {"progression": {"steps": []}}
shoes = {"progression": {"steps": [{"label": "shoes"}]}}

history = [
    {
        "name": "start working out",
        "plan": empty,
        "feedback": None,
    },
    {
        "name": "start working out",
        "plan": shoes,
        "feedback": "I weigh 90 kilograms.",
    },
]

messages = thread_messages(history)
assert messages[0] == {"role": "agent", "text": "The map is empty."}
assert messages[1] == {"role": "user", "text": "I weigh 90 kilograms."}
assert messages[2] == {"role": "agent", "text": "start working out: shoes."}
assert len(messages) == 3

# Leftover planner fields must not become the agent line.
leftover = thread_messages(
    [
        {
            "name": "gym",
            "plan": {
                "clarification": "How often?",
                "suggested_action": "Buy shoes",
                "now": "Put them on",
                "progression": {"steps": [{"label": "warmup"}]},
            },
            "feedback": None,
        },
    ],
)
assert leftover[0] == {"role": "agent", "text": "gym: warmup."}

# A check-in stores "Still working on it. Note: <raw>" and repeats the
# previous surface - the thread should show the raw note and the ack,
# not the labeled blob and not the same map line twice.
check_in = history + [
    {
        "name": "start working out",
        "plan": shoes,
        "feedback": "Still working on it. Note: still working",
    },
]
checked = thread_messages(check_in)
assert checked[3] == {"role": "user", "text": "still working"}
assert checked[4] == {"role": "agent", "text": "Still working on it."}

# map_focus tags each turn so the UI can frame a focused stretch.
same = {"progression": {"steps": []}}
focused = [
    {
        "name": "becoming a developer",
        "plan": same,
        "feedback": None,
    },
    {
        "name": "becoming a developer",
        "plan": same,
        "feedback": "what is this?",
        "map_focus": "concept 4",
        "focus_step_id": "p2",
    },
    {
        "name": "becoming a developer",
        "plan": same,
        "feedback": "make 3 ideas",
        "map_focus": "concept 4",
        "focus_step_id": "p2",
    },
    {
        "name": "becoming a developer",
        "plan": same,
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

# Map edits belong in Status, not the Talk thread (same as past_turns).
with_map = [
    {"name": "House", "plan": empty, "feedback": None},
    {
        "name": "House",
        "plan": {"progression": {"steps": [{"label": "Rooms"}]}},
        "feedback": "Added step: Rooms",
        "event": "node_added",
    },
    {
        "name": "House",
        "plan": {"progression": {"steps": [{"label": "Rooms"}]}},
        "feedback": "Sure. Note: what next?",
        "event": "chat",
    },
]
map_msgs = thread_messages(with_map)
assert [m["text"] for m in map_msgs] == [
    "The map is empty.",
    "what next?",
    "Sure.",
]
assert not any("Added step" in (m.get("text") or "") for m in map_msgs)

print("OK - thread_messages() builds You/Agent lines from history")
