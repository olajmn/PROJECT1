"""
Smallest possible vertical-slice experiment for architecture-v4:

    USER -> LLM1 -> LLM2 -> LLM3 -> Planning (unmodified) -> LLM1 -> USER

Not a product, not a UI, not Flask - a terminal loop whose only job is
to test whether the boundary in docs/architecture-v4.md actually holds
up once real text flows through it. Planning itself
(backend/planning/) is called exactly as it already was verified to
work in the previous checkpoint - nothing in it is touched here.

One thing deliberately lives in THIS file, not in any LLM module or in
Planning, because it is harness/orchestration glue, not reasoning:

- Which existing Planning function to call (create_goal vs.
  apply_feedback) - decided by simple session state (is there already
  an active goal in this terminal session), never by an LLM judgment.
  A real system would need a real answer for this; this experiment
  deliberately uses the crudest one that still lets more than one kind
  of turn be tested.

Turning a Planning record into what LLM1/a UI is allowed to see
(surface_text()/to_planning_node()) is NOT this file's job - see
backend/manifestation.py, shared by this CLI and server.py so there is
one translation, not two.

Run from v4/ (this directory), with v4's own venv:
    .venv/bin/python cli.py
"""

from backend.llm1.interface import respond
from backend.llm2.parser import understand
from backend.llm3.select import select_capability
from backend.manifestation import surface_text, to_planning_node
from backend.planning.goal.resolver import get_latest_for_goal
from backend.planning.plan.planner import apply_feedback, create_goal


class Session:
    """The crude, harness-only state described in the module
    docstring - not a designed concept, just enough to run more than
    one kind of turn in one experiment session."""

    def __init__(self):
        self.current_goal_id: int | None = None


def process_turn(session: Session, user_text: str) -> dict:
    """Runs one turn through the full chain and returns a small trace
    - not just the reply - so a caller (the CLI loop, or an experiment
    script) can inspect what each stage actually produced."""
    understanding = understand(user_text)
    capability = select_capability(understanding)

    if capability != "planning":
        reply = respond(user_text, None)
        return {
            "understanding": understanding, "capability": capability,
            "surface": None, "node": None, "reply": reply, "goal_id": None,
        }

    if session.current_goal_id is None:
        record = create_goal(user_text, "", "")
        session.current_goal_id = record["goal_id"]
    else:
        latest = get_latest_for_goal(session.current_goal_id)
        record = apply_feedback(latest, user_text)

    surface = surface_text(record)
    node = to_planning_node(record)
    reply = respond(user_text, surface)
    return {
        "understanding": understanding, "capability": capability,
        "surface": surface, "node": node, "reply": reply,
        "goal_id": session.current_goal_id,
    }


def main() -> None:
    print("v4 experiment - USER -> LLM1 -> LLM2 -> LLM3 -> Planning. Ctrl+C to quit.\n")
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
            result = process_turn(session, user_text)
        except Exception as e:  # an experiment script must not die on one bad turn
            print(f"Agent: (error this turn: {e})\n")
            continue
        print(f"Agent: {result['reply']}\n")


if __name__ == "__main__":
    main()
