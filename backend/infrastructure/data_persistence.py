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

Full history: docs/06-development.md, 2026-08-21/23/26.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.json"
VISIONS_FILE = DATA_DIR / "visions.json"

# The only user_id that exists today - see module docstring. Not a
# counter like goal_id: there is exactly one person using this app.
DEFAULT_USER_ID = 1

# ============================================================
# 1. Setup & legacy normalization
# ============================================================


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


# ============================================================
# 2. Goal/Plan persistence
# ============================================================


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
    "right_now" action, which led the agent to replan. None for a brand
    new goal that has no prior feedback yet.

    `duration` is the free-text span the user asked this plan to cover
    (e.g. "30 minutes", "this week"), if they gave one - see
    plan.generate_plan(). Stored so the history shows what was
    actually asked for, not just what came back.

    `completed` marks the whole goal (not just one "right_now" step) as
    done - the user said so explicitly, via the "Goal complete" button,
    rather than the agent guessing it from a missing next action. See
    docs/06-development.md, 2026-08-19 entry, for why this exists.

    `goal_id` is the goal's real identity, separate from its display
    text (see backend/goals/goal/resolver.py's get_latest_for_all_goals()). Pass the existing goal_id when this record
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
    description ONCE (see frozen_duration.py §1 - Freezing a duration),
    stored as-is rather than re-derived from "now" on every later page
    render - re-deriving it live would silently reset a countdown like
    "within the next 1 hour" to a full hour on every refresh, instead
    of counting down from when the goal was actually created. Callers
    should compute a fresh one when a genuinely new plan/timeframe decision is being
    made (a new goal, or "continue an existing goal" with a new
    duration), and otherwise pass the PREVIOUS record's frozen_duration
    through unchanged (a replan after feedback keeps the same
    timeframe, it doesn't restart it) - see devtools/app.py's
    /goal and /feedback routes.

    `current_step` is the index into `plan.steps` (see backend/goals/plan/step_generator.py's
    `generate_steps()`) that "Action (right now)" actually points at -
    "right now" isn't its own independent thing once a goal has steps,
    it's just `plan.steps[current_step]` (see docs/06-development.md's
    "Plan as an ordered step list" entry, and devtools/app.py's
    /step route, which is the only thing that ever advances it). 0 (the
    first step) by default - matches `plan.steps[0]` always equaling
    `plan.right_now` (see step_generator.generate_steps()), so a goal with no steps at
    all, or one that's never had this touched, behaves exactly as
    before.

    `vision_id` (added 2026-08-26) optionally links this goal to a
    Vision - broader, cross-goal context, not part of the operational
    goal -> plan -> action -> feedback loop itself (see
    docs/03-architecture.md § Long-term architecture). None is the
    normal case: most goals have no vision. Like `goal_id`, this is an
    identity reference, never invented by a caller - pass an id from
    save_vision()/load_visions(), or an existing record's own
    `vision_id` to carry it forward unchanged across a replan (a goal's
    vision doesn't change just because its plan does - same reasoning
    `frozen_duration` is carried forward rather than recomputed).

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
        # in this project (backend/foundation/time/'s whole resolution/
        # bar/countdown system uses datetime.now(), local). Records
        # saved before 2026-08-21 stored this in UTC instead; see
        # resolver.created_at_key() for how mixed-era history is still
        # sorted correctly despite the format change.
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


# ============================================================
# 3. Vision
# ============================================================
#
# A separate, much smaller store - see this module's docstring for why
# it isn't part of the goal/plan records above. No normalization, no
# backfill: nothing saved before this existed could have a vision_id,
# so there's no legacy shape to migrate.
# ============================================================


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
    parameter and docs/03-architecture.md § Long-term architecture).

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
