"""
Data Persistence
================

Local storage for goals, plans, and Visions. Everything is stored as a
simple JSON file: a list of records, oldest first - no server, no
schema migrations, just dictionaries written to disk. Data lives in
data/plans.json and data/visions.json, both git-ignored (see
.gitignore) - this is personal information, never committed.

Contents
1. Setup & legacy normalization
2. Goal/Plan persistence
3. Vision

Goal identity/grouping lives in goal/resolver.py, not here - see
that module's docstring for why goal_id minting/backfill stays in this
file regardless.

Vision is a second, much smaller store of the same shape as a goal's
identity - a plain list of {id, text, created_at} records, no history,
no normalization, no backfill (nothing predates it). A Goal record MAY
carry an optional `vision_id` into this list; most won't, and that's
normal, not a gap. Not its own module the way resolver.py is - there's
no grouping/derivation logic here, just create/list/get, so a separate
file would be structure without a use for it yet (see
docs/05-decisions.md for the fuller reasoning).

Every record also carries a `user_id`, always DEFAULT_USER_ID for now -
there is exactly one person using this app (real multi-user support is
explicitly deferred past MVP, needs proper auth + encryption first; see
docs/05-decisions.md). Not the start of an accounts system - a stable
field so existing history won't need a migration if multi-user support
is ever built. Unlike goal_id, there is no minting/counter for it:
there's only ever one value.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"
VISIONS_FILE = DATA_DIR / "visions.json"

# The only user_id that exists today - see module docstring.
DEFAULT_USER_ID = 1

# Setup & legacy normalization


def ensure_data_dir() -> None:
    """Create data/ if it doesn't exist yet. Safe to call repeatedly."""
    DATA_DIR.mkdir(exist_ok=True)


# one_year/one_month/this_week/this_hour/this_minute/right_now renamed
# to year/month/week/hour/minute/now (PLAN_KEYS, planner.py) once those
# turned out to name plan-record slots (time levels), not literal
# durations or deictic phrases - existing saved records still have the
# old names.
_LEGACY_HORIZON_KEY_RENAMES = {
    "one_year": "year", "one_month": "month", "this_week": "week",
    "this_hour": "hour", "this_minute": "minute", "right_now": "now",
}


def _normalize_plan(plan) -> dict:
    """
    Convert a legacy free-text plan (from before the switch to structured
    JSON) into the current dict shape, and remap any pre-rename horizon
    key names a dict-shaped plan still has (_LEGACY_HORIZON_KEY_RENAMES),
    so every caller only ever sees the current shape/names.
    """
    if not isinstance(plan, dict):
        return {
            "year": "", "month": "", "week": "",
            "today": "", "hour": "", "minute": "",
            "now": plan,
        }
    return {_LEGACY_HORIZON_KEY_RENAMES.get(key, key): value for key, value in plan.items()}


def _backfill_goal_ids(records: list[dict]) -> None:
    """
    Records saved before `goal_id` existed have no identity beyond their
    `goal` text - board grouping used to be done on that text directly
    (fragile: "take a shower" / "take shower" / "ta en dusj" all counted
    as different goals). Give each legacy record a goal_id, one per
    distinct goal text, assigned in first-appearance order - this
    reproduces exactly the grouping the board view used before goal_id
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


# Goal/Plan persistence


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
    vision_id: int | None = None,
) -> dict:
    """
    Append a new goal+plan record to history and persist it to disk.

    `feedback` is the user's feedback (if any) that caused this plan to
    be created - i.e. what they said about the *previous* plan's
    "now" action, which led the agent to replan. None for a brand
    new goal that has no prior feedback yet.

    `duration` is the free-text span the user asked this plan to cover
    (e.g. "30 minutes", "this week"), if they gave one - see
    plan.generate_plan(). Stored so the history shows what was
    actually asked for, not just what came back.

    `completed` marks the whole goal (not just one "now" step) as
    done - the user said so explicitly, rather than the agent guessing
    it from a missing next action.

    `goal_id` is the goal's real identity, separate from its display
    text. Pass the existing goal_id to continue a goal already in
    history; leave it None for a genuinely new goal (one is minted
    here). Never invent a goal_id - always get it from an existing
    record or this function's return value.

    There is no `user_id` parameter (unlike `goal_id`): every record is
    stamped with DEFAULT_USER_ID directly, since there is exactly one
    user of this app today - see module docstring. Not exposed as a
    choice callers could get wrong, because there is nothing to choose
    yet.

    `frozen_duration` is `duration` resolved to a real start/end/
    description ONCE (see frozen_duration.py §1), stored as-is rather
    than re-derived from "now" on every page render - re-deriving it
    live would silently reset a countdown like "within the next 1
    hour" on every refresh instead of counting down from creation.
    Compute a fresh one only for a genuinely new plan/timeframe
    decision; otherwise pass the previous record's value through
    unchanged (a replan after feedback keeps the same timeframe).

    `current_step` is the index into `plan.steps` that "Action (right
    now)" points at - `plan.steps[current_step]`, not an independent
    value. 0 by default, matching `plan.steps[0]` always equaling
    `plan.now`.

    `vision_id` optionally links this goal to a Vision - broader,
    cross-goal context, not part of the operational goal -> plan ->
    action -> feedback loop (see docs/03-architecture.md § Vision).
    None is the normal case. Like `goal_id`, never invented by a caller
    - pass an id from save_vision()/load_visions(), or carry the
    existing record's own `vision_id` forward unchanged across a
    replan (same reasoning as `frozen_duration`).

    Returns the record that was saved (useful for confirming to the user).
    """
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "user_id": DEFAULT_USER_ID,
        "goal_id": goal_id if goal_id is not None else _next_goal_id(records),
        "vision_id": vision_id,
        "goal": goal,
        "plan": plan,
        "feedback": feedback,
        "duration": duration,
        "frozen_duration": frozen_duration,
        "current_step": current_step,
        "completed": completed,
        # Local time, naive (no tzinfo) - matches every other timestamp
        # in this project. Older records stored this in UTC; see
        # resolver.created_at_key() for sorting mixed-era history.
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


# Vision


def _load_all_visions() -> list[dict]:
    """Read every saved vision from disk. Empty list if the file doesn't exist yet."""
    if not VISIONS_FILE.exists():
        return []
    try:
        with open(VISIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{VISIONS_FILE} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e


def _save_all_visions(visions: list[dict]) -> None:
    """Write the full list of visions back to disk - same atomic-rename approach as _save_all()."""
    ensure_data_dir()
    tmp_file = VISIONS_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(visions, f, indent=2, ensure_ascii=False)
    tmp_file.replace(VISIONS_FILE)


def _next_vision_id(visions: list[dict]) -> int:
    """One higher than the largest vision id in history, or 1 if there are none yet."""
    existing = [v["id"] for v in visions]
    return max(existing, default=0) + 1


def save_vision(text: str) -> dict:
    """
    Create a new Vision and persist it - broader, cross-goal context a
    Goal can optionally reference (see save_plan()'s `vision_id`
    parameter and docs/03-architecture.md § Vision).

    No history, no revisions: unlike a goal/plan record, a vision is a
    single mutable fact ("this is what the text currently says"), not
    a chain - there's nothing here yet that needs to look back at how
    a vision's wording changed over time. Editing/deleting an existing
    vision is intentionally not built yet (see docs/05-decisions.md) -
    this only ever appends a new one.

    Returns the record that was saved.
    """
    visions = _load_all_visions()
    record = {
        "id": _next_vision_id(visions),
        "user_id": DEFAULT_USER_ID,
        "text": text,
        "created_at": datetime.now().isoformat(),
    }
    visions.append(record)
    _save_all_visions(visions)
    return record


def load_visions() -> list[dict]:
    """Return every saved Vision, oldest first."""
    return _load_all_visions()


def get_vision(vision_id: int) -> dict | None:
    """Return the Vision with this id, or None if it doesn't exist (e.g. a stale reference)."""
    for vision in _load_all_visions():
        if vision["id"] == vision_id:
            return vision
    return None
