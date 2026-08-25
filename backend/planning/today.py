"""
"Today's task" - shows just the immediate next action from the most
recently saved plan, instead of the whole plan.

This is the "zoom all the way in" step from the project vision: the user
shouldn't have to re-read the whole plan every day, just be told what to
do right now.

Run from the PROJECT ROOT: .venv/bin/python -m backend.agent.specialized.today
"""

from backend.infrastructure.data_persistence import get_latest_plan

if __name__ == "__main__":
    latest = get_latest_plan()

    if latest is None:
        print("No plan saved yet. Run plan.py first.")
    else:
        print(f"Goal: {latest['goal']}")
        print(f"\nRight now: {latest['plan']['right_now']}")
