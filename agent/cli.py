"""
Smallest possible vertical-slice experiment for docs/v4-migration-decision.md:

    USER -> Voice -> Describe -> LLM3 -> Planning -> Voice -> USER

Not a product, not a UI, not Flask - a terminal loop whose only job is
to test whether the boundary in docs/v4-migration-decision.md actually holds
up once real text flows through it. Planning itself
(backend/planning/) is called exactly as it already was verified to
work in the previous checkpoint - nothing in it is touched here.

One thing deliberately lives in THIS file, not in any LLM module or in
Planning, because it is harness/orchestration glue, not reasoning:

- Which existing Planning function to call (create_goal vs.
  route_note) - decided by simple session state (is there already
  an active goal in this terminal session), never by an LLM judgment.
  A real system would need a real answer for this; this experiment
  deliberately uses the crudest one that still lets more than one kind
  of turn be tested.

Turning a Planning record into what LLM1/a UI is allowed to see
(surface_text()/to_planning_node()) is NOT this file's job - see
backend/manifestation.py, shared by this CLI and server.py so there is
one translation, not two.

Run from agent/ (this directory), with agent/'s own venv:
    .venv/bin/python cli.py
"""

from backend.infrastructure.data_persistence import start_session
from backend.llm_roles.voice import respond
from backend.llm_roles.describe import describe
from backend.llm3.select import select_capability
from backend.manifestation import surface_text, to_planning_node
from backend.planning.feedback.route_note import route_note
from backend.planning.goal.lifecycle import create_goal
from backend.planning.goal.resolver import get_latest_for_goal


class ChatFocus:
    """Which goal, if any, the free-conversation path is currently
    focused on - the crude, harness-only state described in the module
    docstring - not a designed concept, just enough to run more than
    one kind of turn in one experiment session. Not itself persisted;
    lives only as long as the process does. Scoped inside a Session
    (below), not a sibling fact bolted onto it - split out 2026-09-12
    once the two had ended up sharing one Python object and confusing
    the (already renamed) "chat focus" vs. "Session" naming split at
    the API/UI layer - see docs/04-current-state.md § 8."""

    def __init__(self):
        self.goal_id: int | None = None


class Session:
    """A real run of this process (main() below, or server.py's
    module-level `session`) - persists a Session record
    (data_persistence.start_session(), added 2026-09-12) once per
    construction, not per turn, and owns this run's ChatFocus.

    `id`/`started_at` mirror the persisted record so a caller
    (server.py's GET /api/sessions) can expose them without re-reading
    the file; that same route derives "what happened" from
    load_history()/load_visions() filtered by this window, rather than
    this class logging anything itself - see docs/04-current-state.md
    § 8. `chat_focus` is everything that happens to the free-
    conversation path's current goal *during* this Session - a Session
    is the overarching thing; chat focus is one aspect of it, not a
    separate, equally-important fact living alongside it."""

    def __init__(self):
        record = start_session()
        self.id: int = record["id"]
        self.started_at: str = record["started_at"]
        self.chat_focus = ChatFocus()


def process_turn(chat_focus: ChatFocus, user_text: str) -> dict:
    """Runs one turn through the full chain and returns a small trace
    - not just the reply - so a caller (the CLI loop, or an experiment
    script) can inspect what each stage actually produced.

    Takes a ChatFocus, not a whole Session - this function only ever
    needs to know which goal the chat is pointed at, never a Session's
    own id/started_at, so it doesn't need to know Session exists at
    all (see main()'s own `session.chat_focus` call site)."""
    understanding = describe(user_text)
    capability = select_capability(understanding)

    if capability != "planning":
        reply = respond(user_text, None)
        return {
            "understanding": understanding, "capability": capability,
            "surface": None, "node": None, "reply": reply, "goal_id": None,
        }

    if chat_focus.goal_id is None:
        record = create_goal(user_text, "", "")
        chat_focus.goal_id = record["goal_id"]
    else:
        latest = get_latest_for_goal(chat_focus.goal_id)
        record = route_note(latest, user_text)

    surface = surface_text(record)
    node = to_planning_node(record)
    reply = respond(user_text, surface)
    return {
        "understanding": understanding, "capability": capability,
        "surface": surface, "node": node, "reply": reply,
        "goal_id": chat_focus.goal_id,
    }


def main() -> None:
    print("USER -> Voice -> Describe -> LLM3 -> Planning experiment. Ctrl+C to quit.\n")
    session = Session()
    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        try:
            result = process_turn(session.chat_focus, user_text)
        except Exception as e:  # an experiment script must not die on one bad turn
            # A friendly, deterministic fallback, not the raw exception
            # text - model.client.call_with_retry already
            # absorbs the model-shape hiccups this is most likely to
            # be; what reaches here is either a genuinely persistent
            # failure or something unrelated to the model entirely,
            # and a raw Python exception string has no place standing
            # in as "the agent's reply" either way. Printed to the
            # terminal alongside the friendly line, for whoever is
            # actually debugging this run.
            print(f"  (debug: {e})")
            print("Agent: That took longer than expected - try again in a moment.\n")
            continue
        print(f"Agent: {result['reply']}\n")


if __name__ == "__main__":
    main()
