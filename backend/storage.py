"""
Local storage for goals and plans.

Everything is stored as a simple JSON file: a list of records, oldest
first. This is intentionally the simplest possible "database" - no
server, no schema migrations, just a list of dictionaries written to disk.

Data lives in data/plans.json, which is git-ignored (see .gitignore) -
this is personal information and must never be committed to a repository.

This module normalizes legacy shapes on read: records saved before the
switch to structured JSON (v0.1) had `plan` as a plain string; _load_all()
converts those into the current dict shape (see plan.PLAN_KEYS) so every
caller - today.py, the templates, plan.py - can always assume `plan` is
a dict with those keys, without special-casing it themselves.

Goal identity/grouping (get_board() and friends) lives in backend/goal.py,
not here - see that module's docstring for why goal_id minting/backfill
stays in this file regardless.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"


def ensure_data_dir() -> None:
    """Create data/ if it doesn't exist yet. Safe to call repeatedly."""
    DATA_DIR.mkdir(exist_ok=True)


def _normalize_plan(plan) -> dict:
    """
    Convert a legacy free-text plan (from before the switch to structured
    JSON) into the current dict shape, so every caller only ever sees one
    shape. Dict plans pass through unchanged.
    """
    if isinstance(plan, dict):
        return plan
    return {"one_year": "", "one_month": "", "this_week": "", "right_now": plan}


def _backfill_goal_ids(records: list[dict]) -> None:
    """
    Records saved before `goal_id` existed have no identity beyond their
    `goal` text - board grouping used to be done on that text directly
    (fragile: "take a shower" / "take shower" / "ta en dusj" all counted
    as different goals). Give each legacy record a goal_id, one per
    distinct goal text, assigned in first-appearance order - this
    reproduces exactly the grouping get_board() used before goal_id
    existed, so old history's board layout doesn't shift silently.

    Records that already have a goal_id (created after this change) are
    left untouched. Mutates records in place; the result is only
    persisted once something calls save_plan() and _save_all() writes
    the full list back out - same pattern as _normalize_plan().
    """
    seen: dict[str, int] = {}
    next_id = 1
    for record in records:
        if record.get("goal_id"):
            continue
        if record["goal"] not in seen:
            seen[record["goal"]] = next_id
            next_id += 1
        record["goal_id"] = seen[record["goal"]]


def _next_goal_id(records: list[dict]) -> int:
    """One higher than the largest goal_id in history, or 1 if there are none yet."""
    existing = [r["goal_id"] for r in records if r.get("goal_id")]
    return max(existing, default=0) + 1


def _load_all() -> list[dict]:
    """Read every saved record from disk, normalizing legacy plan shapes.

    Returns an empty list if the file doesn't exist yet (e.g. this is
    the very first run and nothing has been saved).
    """
    if not PLANS_FILE.exists():
        return []
    try:
        with open(PLANS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{PLANS_FILE} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e

    _backfill_goal_ids(records)
    for record in records:
        record["plan"] = _normalize_plan(record["plan"])
    return records


def _save_all(records: list[dict]) -> None:
    """
    Write the full list of records back to disk, creating data/ if needed.

    Writes to a temp file and renames it into place - a rename is atomic
    on POSIX filesystems (macOS/Linux), so a crash mid-write can never
    leave plans.json half-written/corrupted; the old file stays intact
    until the new one is fully written.
    """
    ensure_data_dir()
    tmp_file = PLANS_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    tmp_file.replace(PLANS_FILE)


def save_plan(
    goal: str,
    plan: dict,
    feedback: str | None = None,
    duration: str | None = None,
    completed: bool = False,
    goal_id: int | None = None,
) -> dict:
    """
    Append a new goal+plan record to history and persist it to disk.

    `feedback` is the user's feedback (if any) that caused this plan to
    be created - i.e. what they said about the *previous* plan's
    "right_now" action, which led the agent to replan. None for a brand
    new goal that has no prior feedback yet.

    `duration` is the free-text span the user asked this plan to cover
    (e.g. "30 minutes", "this week"), if they gave one - see
    plan.generate_plan(). Stored so the history shows what was
    actually asked for, not just what came back.

    `completed` marks the whole goal (not just one "right_now" step) as
    done - the user said so explicitly, via the "Goal complete" button,
    rather than the agent guessing it from a missing next action. See
    docs/11-experiments.md, 2026-08-19 entry, for why this exists.

    `goal_id` is the goal's real identity, separate from its display
    text (see backend/goal.py's get_board()). Pass the existing goal_id when this record
    continues a goal already in history (e.g. a replan after feedback,
    or explicitly picking "continue an existing goal"); leave it None
    for a genuinely new goal, and one is minted here. Callers should
    never invent a goal_id themselves - always get it from an existing
    record or from this function's return value.

    Returns the record that was saved (useful for confirming to the user).
    """
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "goal_id": goal_id if goal_id is not None else _next_goal_id(records),
        "goal": goal,
        "plan": plan,
        "feedback": feedback,
        "duration": duration,
        "completed": completed,
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
