"""
Free-conversation turn — Describe → Node 3 → Project or Voice alone.

Used by cli.py's terminal loop and server.py's POST /api/message.
Project-scoped chat (goal id already known) lives in
backend.project.panes.chat.turn instead.
"""

# Contents
#  1. Session state
#      - ChatFocus
#      - Session
#
#  2. Free-conversation turn
#      - process_turn()

from backend.store.session import start_session
from backend.agent.llm_roles.voice import respond
from backend.agent.llm_roles.describe import describe
from backend.agent.llm3.select import select_capability
from backend.agent.manifestation import surface_text, to_planning_node
from backend.project.panes.chat.feedback.route_note import route_note
from backend.project.panes.create.lifecycle import create_goal
from backend.project.panes.create.resolver import get_latest_for_goal


# ============================================================
# 1. Session state
# ============================================================


class ChatFocus:
    """Which goal, if any, the free-conversation path is currently
    focused on - crude session state so more than one kind of turn
    can run in one process. Not persisted; lives only as long as the
    process does. Owned by Session below.
    """

    def __init__(self):
        self.goal_id: int | None = None


class Session:
    """One run of the free-conversation process (cli main, or
    server.py's module-level session) — persists a Session record via
    start_session() once per construction, and owns this run's
    ChatFocus.
    """

    def __init__(self):
        record = start_session()
        self.id: int = record["id"]
        self.started_at: str = record["started_at"]
        self.chat_focus = ChatFocus()


# ============================================================
# 2. Free-conversation turn
# ============================================================


def process_turn(chat_focus: ChatFocus, user_text: str) -> dict:
    """One free-conversation turn through Describe → select → Project
    or Voice. Returns a small trace (not just the reply).

    Takes ChatFocus, not Session — only needs which goal the chat is
    pointed at.
    """
    understanding = describe(user_text)
    capability = select_capability(understanding)

    if capability != "project":
        reply = respond(user_text, None)
        return {
            "understanding": understanding, "capability": capability,
            "surface": None, "node": None, "reply": reply,
            "project_id": None, "goal_id": None,
        }

    if chat_focus.goal_id is None:
        record = create_goal(user_text, "", "")
        chat_focus.goal_id = record["project_id"]
    else:
        latest = get_latest_for_goal(chat_focus.goal_id)
        record = route_note(latest, user_text)

    surface = surface_text(record)
    node = to_planning_node(record)
    reply = respond(user_text, surface)
    pid = chat_focus.goal_id
    return {
        "understanding": understanding, "capability": capability,
        "surface": surface, "node": node, "reply": reply,
        "project_id": pid,
        "goal_id": pid,  # deprecated mirror
    }
