"""
Local storage for goals and plans.

Everything is stored as a simple JSON file: a list of records, oldest
first. This is intentionally the simplest possible "database" - no
server, no schema migrations, just a list of dictionaries written to disk.

Data lives in data/plans.json, which is git-ignored (see .gitignore) -
this is personal information and must never be committed to a repository.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"


def _load_all() -> list[dict]:
    """Read every saved record from disk.

    Returns an empty list if the file doesn't exist yet (e.g. this is
    the very first run and nothing has been saved).
    """
    if not PLANS_FILE.exists():
        return []
    with open(PLANS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all(records: list[dict]) -> None:
    """Write the full list of records back to disk, creating data/ if needed."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(PLANS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def save_plan(goal: str, plan: str, feedback: str | None = None) -> dict:
    """
    Append a new goal+plan record to history and persist it to disk.

    `feedback` is the user's feedback (if any) that caused this plan to
    be created - i.e. what they said about the *previous* plan's
    "right_now" action, which led the agent to replan. None for a brand
    new goal that has no prior feedback yet.

    Returns the record that was saved (useful for confirming to the user).
    """
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "goal": goal,
        "plan": plan,
        "feedback": feedback,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    records.append(record)
    _save_all(records)
    return record


def load_history() -> list[dict]:
    """Return every saved goal+plan record, oldest first."""
    return _load_all()


def get_latest_plan() -> dict | None:
    """Return the most recently saved record, or None if there's no history yet."""
    records = _load_all()
    return records[-1] if records else None
