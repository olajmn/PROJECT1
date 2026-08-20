"""
Local storage for goals and plans.

Everything is stored as a simple JSON file: a list of records, oldest
first. This is intentionally the simplest possible "database" - no
server, no schema migrations, just a list of dictionaries written to disk.

Data lives in data/plans.json, which is git-ignored (see .gitignore) -
this is personal information and must never be committed to a repository.

This module also owns the plan SHAPE: the four time-horizon keys are
defined once here (PLAN_KEYS/HORIZON_LABELS) instead of being duplicated
across the prompts, the templates, and every reader. Records saved
before the switch to structured JSON (v0.1) had `plan` as a plain
string; _load_all() normalizes those into the current dict shape so
every caller - today.py, the templates, goal_to_plan.py - can always
assume `plan` is a dict with these keys, without special-casing it
themselves.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"

# The plan schema, defined once. generate_plan()/replan() ask the LLM
# for exactly these keys; the templates iterate this same list to render
# every horizon in the same order.
PLAN_KEYS = ("one_year", "one_month", "this_week", "right_now")
HORIZON_LABELS = {
    "one_year": "1 year",
    "one_month": "1 month",
    "this_week": "This week",
    "right_now": "Right now",
}


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
    goal_to_plan.generate_plan(). Stored so the history shows what was
    actually asked for, not just what came back.

    `completed` marks the whole goal (not just one "right_now" step) as
    done - the user said so explicitly, via the "Goal complete" button,
    rather than the agent guessing it from a missing next action. See
    docs/11-experiments.md, 2026-08-19 entry, for why this exists.

    `goal_id` is the goal's real identity, separate from its display
    text (see get_board()). Pass the existing goal_id when this record
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


def get_history_for_goal(goal_id: int) -> list[dict]:
    """
    Return every record for one specific goal_id, oldest first - the
    goal's full back-and-forth: the original goal, then each
    feedback-and-replan round in order.

    A goal's history already *is* a conversation - each record's
    `feedback` is what the user said about the previous record's
    `right_now`, and its own `right_now` is the agent's reply - this
    just returns that chain so a template can render it as one instead
    of only ever showing the latest snapshot. See
    devtools/templates/_active_goal.html.
    """
    return [r for r in _load_all() if r["goal_id"] == goal_id]


def get_latest_for_goal(goal_id: int) -> dict | None:
    """
    Return the most recent record for one specific goal_id, or None if
    no record has that goal_id.

    Needed once more than one goal can be active at a time (see
    docs/10-development.md, 2026-08-20): get_latest_plan() answers "what
    was touched most recently, across every goal", which stops being
    the right question the moment two goals are both active side by
    side on the board - giving feedback on one must never silently act
    on whichever goal happens to be globally newest.
    """
    for record in reversed(_load_all()):
        if record["goal_id"] == goal_id:
            return record
    return None


def get_board() -> dict:
    """
    Group history into "active" and "completed" goals, for a board view
    (see docs/10-development.md, 2026-08-19).

    A "goal" isn't its own stored entity - it's a chain of records
    sharing the same `goal_id`, created by generate_plan() and then
    extended by replan() each time feedback comes in (see save_plan()).
    So the only way to know a goal's current state is to find its most
    recent record. Records are loaded oldest-first, so iterating in
    order and overwriting by goal_id naturally leaves the latest record
    per goal.

    Grouping by goal_id (not `goal` text) is what makes this reliable:
    retyping a goal's text slightly differently ("take a shower" vs.
    "take shower") used to fragment it into separate board entries.
    goal_id is a stable identity assigned once and carried forward
    regardless of text - see docs/12-decisions.md, 2026-08-20.

    Returns {"active": [...], "completed": [...]}, each a list of
    records (latest state only, one per distinct goal).
    """
    latest_by_goal: dict[int, dict] = {}
    for record in _load_all():
        latest_by_goal[record["goal_id"]] = record

    # .get(), not [] - records saved before the "completed" field
    # existed don't have the key at all.
    active = [r for r in latest_by_goal.values() if not r.get("completed")]
    completed = [r for r in latest_by_goal.values() if r.get("completed")]
    return {"active": active, "completed": completed}
