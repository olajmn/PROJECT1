"""
Read-only view of the current Action - shows just the immediate
`right_now` step from the most recently saved plan, instead of the
whole plan. Never generates or changes a plan, never talks to Ollama -
purely reads what planner.py already produced (see
data_persistence.get_latest_plan()).

This is the "zoom all the way in" step from the project vision: the user
shouldn't have to re-read the whole plan every day, just be told what to
do right now.

Named for the "Action" concept (architecture_foundation/goals/action/
README.md), not "today" - avoids colliding with PLAN_KEYS' own,
unrelated `"today"` horizon. Renamed from today.py, 2026-08-27.

Run from the PROJECT ROOT: .venv/bin/python -m backend.planning.action_reader
"""

from backend.infrastructure.data_persistence import get_latest_plan

if __name__ == "__main__":
    latest = get_latest_plan()

    if latest is None:
        print("No plan saved yet. Run planner.py first.")
    else:
        print(f"Goal: {latest['goal']}")
        print(f"\nRight now: {latest['plan']['right_now']}")
