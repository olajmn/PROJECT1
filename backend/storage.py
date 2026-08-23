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

Every record also carries a `user_id` (added 2026-08-23), always
DEFAULT_USER_ID for now - there is exactly one person using this app
(see docs/12-decisions.md: real multi-user support is explicitly
deferred past MVP, needs proper auth + encryption first). This is
deliberately NOT the start of an accounts system - it's a stable field
added now so that if/when multi-user support is ever built, existing
history doesn't need a migration to grow one. Unlike goal_id, there is
no minting/counter for it: there's only ever one value.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"

# The only user_id that exists today - see module docstring. Not a
# counter like goal_id: there is exactly one person using this app.
DEFAULT_USER_ID = 1


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
    return {
        "one_year": "", "one_month": "", "this_week": "",
        "today": "", "this_hour": "", "this_minute": "",
        "right_now": plan,
    }


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


def _backfill_user_ids(records: list[dict]) -> None:
    """
    Records saved before `user_id` existed get DEFAULT_USER_ID - unlike
    _backfill_goal_ids(), there's no grouping/counting to do: every
    record belongs to the same single user, so there's only one value
    to fill in. Mutates records in place, same as _backfill_goal_ids().
    """
    for record in records:
        if not record.get("user_id"):
            record["user_id"] = DEFAULT_USER_ID


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
    _backfill_user_ids(records)
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
    frozen_duration: dict | None = None,
    current_step: int = 0,
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

    There is no `user_id` parameter (unlike `goal_id`): every record is
    stamped with DEFAULT_USER_ID directly, since there is exactly one
    user of this app today - see module docstring. Not exposed as a
    choice callers could get wrong, because there is nothing to choose
    yet.

    `frozen_duration` is `duration` resolved to a real start/end/
    description ONCE (see backend/timeperiod.py's freeze_duration()),
    stored as-is rather than re-derived from "now" on every later page
    render - fixes a real bug, 2026-08-21: a forward-looking duration
    like "within the next 1 hour" was silently resetting its countdown
    to a full hour on every page refresh, because it used to be
    re-resolved against the current moment each time instead of the
    moment the goal was actually created. Callers should compute a
    fresh one when a genuinely new plan/timeframe decision is being
    made (a new goal, or "continue an existing goal" with a new
    duration), and otherwise pass the PREVIOUS record's frozen_duration
    through unchanged (a replan after feedback keeps the same
    timeframe, it doesn't restart it) - see backend/devtools/app.py's
    /goal and /feedback routes.

    `current_step` is the index into `plan.steps` (see backend/plan.py's
    `_generate_steps()`) that "Task (right now)" actually points at -
    "right now" isn't its own independent thing once a goal has steps,
    it's just `plan.steps[current_step]` (see docs/13-ideas-parking-lot.md's
    "Plan as an ordered step list" entry, and backend/devtools/app.py's
    /step route, which is the only thing that ever advances it). 0 (the
    first step) by default - matches `plan.steps[0]` always equaling
    `plan.right_now` (see _generate_steps()), so a goal with no steps at
    all, or one that's never had this touched, behaves exactly as
    before.

    Returns the record that was saved (useful for confirming to the user).
    """
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "user_id": DEFAULT_USER_ID,
        "goal_id": goal_id if goal_id is not None else _next_goal_id(records),
        "goal": goal,
        "plan": plan,
        "feedback": feedback,
        "duration": duration,
        "frozen_duration": frozen_duration,
        "current_step": current_step,
        "completed": completed,
        # Local time, naive (no tzinfo) - matches every other timestamp
        # in this project (backend/timeperiod.py's whole resolution/
        # bar/countdown system uses datetime.now(), local). Was UTC
        # since the very first commit for no documented reason (no
        # multi-timezone need in a single-machine personal tool) -
        # switched 2026-08-21 after the mismatch was noticed directly
        # in the log: created_at said "18:24" while the very next line
        # (duration's frozen description) said "now 20:24" for the
        # exact same real moment - correct, just confusing, two
        # different clocks shown side by side for one event.
        "created_at": datetime.now().isoformat(),
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
