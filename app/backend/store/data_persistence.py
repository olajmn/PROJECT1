"""
Local storage for goals, plans, and simulated users (id#N). Goal
history is one JSON object per line in data/plans.jsonl (JSONL);
simulated users are a JSON array in data/users.json (legacy
data/visions.json is promoted on first load). Both git-ignored (see
.gitignore) - this is personal information, never committed. Session
records live in session.py (data/sessions.json). A legacy
data/plans.json array, if still present, is migrated to plans.jsonl on
first load.

Goal identity/grouping lives in goal/resolver.py, not here - see
that module's docstring for why goal_id minting/backfill stays in this
file regardless.

Simulated users are a second, much smaller store of the same shape as
a project's identity - a plain list of {id, text, created_at} records,
no history, no normalization beyond disk promote from visions.json. A
plan record MAY carry an optional `sim_user_id` into this list (legacy
`vision_id` is promoted on load); most won't until Projects assigns
one. Not its own module the way resolver.py is - there's no
grouping/derivation logic here, just create/list/get/archive.

A simulated user can be archived (`archived: True`) - mutates the one
existing record in place. Detaching projects from an archived user
(project_user.archive_user()) is a higher-level decision, not done here.

Every record also carries a stub `user_id`, always DEFAULT_USER_ID for
now - there is exactly one *operator* of this app (auth deferred). That
field is NOT the simulated multi-user filter; that is `sim_user_id`.
Unlike project_id, there is no minting/counter for the stub: there's
only ever one value.
"""

# Contents
#  1. Setup & legacy normalization
#      - DATA_DIR / PLANS_FILE / LEGACY_PLANS_FILE / USERS_FILE /
#        LEGACY_VISIONS_FILE / DEFAULT_USER_ID
#      - ensure_data_dir()
#      - _LEGACY_HORIZON_KEY_RENAMES
#      - _normalize_plan()
#      - _backfill_goal_ids() / _normalize_project_ids() / record_project_id()
#      - _normalize_sim_user_ids()
#      - _backfill_user_ids()
#
#  2. Goal records (plans.jsonl)
#      - _next_goal_id() / _load_all() / _save_all() / _append_record()
#      - save_plan()  (persists project_id + sim_user_id)
#      - stamp_map_focus()
#      - set_project_name()
#      - load_history()
#      - get_latest_plan()
#
#  3. Simulated users (users.json)
#      - _load_all_users() / _save_all_users() / _next_user_id()
#      - save_user()
#      - load_users()
#      - get_user()
#      - archive_user()

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PLANS_FILE = DATA_DIR / "plans.jsonl"
LEGACY_PLANS_FILE = DATA_DIR / "plans.json"
USERS_FILE = DATA_DIR / "users.json"
LEGACY_VISIONS_FILE = DATA_DIR / "visions.json"

# The only stub operator user_id that exists today - see module docstring.
DEFAULT_USER_ID = 1


# ============================================================
# 1. Setup & legacy normalization
# ============================================================


def ensure_data_dir() -> None:
    """Create data/ if it doesn't exist yet. Safe to call repeatedly."""
    DATA_DIR.mkdir(exist_ok=True)


# one_year/one_month/this_week/this_hour/this_minute/right_now renamed
# to year/month/week/hour/minute/now (PLAN_KEYS, judgment/shape.py) once those
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


def record_project_id(record: dict) -> int | None:
    """Canonical project identity on a history record.

    Prefers project_id; falls back to legacy goal_id for un-normalized
    callers. Returns None if neither is set.
    """
    pid = record.get("project_id")
    if pid is not None:
        return int(pid)
    gid = record.get("goal_id")
    if gid is not None:
        return int(gid)
    return None


def _backfill_goal_ids(records: list[dict]) -> None:
    """
    Records saved before any numeric identity existed have no identity
    beyond their `goal` text. Assign one id per distinct goal text, in
    first-appearance order, onto project_id (legacy files used goal_id;
    _normalize_project_ids promotes that).

    Records that already have project_id or goal_id are left untouched.
    """
    seen: dict[str, int] = {}
    next_id = 1
    for record in records:
        if record.get("project_id") or record.get("goal_id"):
            continue
        if record["goal"] not in seen:
            seen[record["goal"]] = next_id
            next_id += 1
        record["project_id"] = seen[record["goal"]]


def _normalize_project_ids(records: list[dict]) -> bool:
    """Promote legacy goal_id → project_id; drop goal_id from memory.

    Returns True if any record still had only goal_id on disk shape
    (caller should rewrite plans.jsonl so grepping shows project_id).
    """
    needed_rewrite = False
    for record in records:
        has_project = record.get("project_id") is not None
        has_goal = record.get("goal_id") is not None
        if has_goal and not has_project:
            record["project_id"] = int(record["goal_id"])
            needed_rewrite = True
        elif has_goal and has_project:
            # Prefer project_id; drop the legacy key.
            needed_rewrite = True
        if "goal_id" in record:
            del record["goal_id"]
            needed_rewrite = True
    return needed_rewrite


def _normalize_sim_user_ids(records: list[dict]) -> bool:
    """Promote legacy vision_id → sim_user_id; drop vision_id from memory.

    Ensures every record has sim_user_id (None when unset). Returns True
    if a disk rewrite is needed so grepping shows sim_user_id.
    """
    needed_rewrite = False
    for record in records:
        has_sim = "sim_user_id" in record
        has_vision = "vision_id" in record
        if has_vision and not has_sim:
            record["sim_user_id"] = record["vision_id"]
            needed_rewrite = True
        elif has_vision and has_sim:
            needed_rewrite = True
        elif not has_sim:
            record["sim_user_id"] = None
            needed_rewrite = True
        if "vision_id" in record:
            del record["vision_id"]
            needed_rewrite = True
    return needed_rewrite


def _backfill_user_ids(records: list[dict]) -> None:
    """
    Records saved before stub `user_id` existed get DEFAULT_USER_ID -
    unlike _backfill_goal_ids(), there's no grouping/counting to do:
    every record belongs to the same operator, so there's only one
    value to fill in. Mutates records in place.
    """
    for record in records:
        if not record.get("user_id"):
            record["user_id"] = DEFAULT_USER_ID


# ============================================================
# 2. Goal records (plans.jsonl)
# ============================================================


def _next_goal_id(records: list[dict]) -> int:
    """One higher than the largest project_id in history, or 1 if none.

    Name kept as _next_goal_id this round (Python symbol rename is a
    follow-up); values are project_id.
    """
    existing = []
    for r in records:
        pid = record_project_id(r)
        if pid is not None:
            existing.append(pid)
    return max(existing, default=0) + 1


def _normalize_records(records: list[dict]) -> tuple[list[dict], bool]:
    """Backfill ids and normalize plan shapes in place.

    Returns (records, needs_disk_rewrite) — rewrite when goal_id was
    promoted to project_id or vision_id to sim_user_id.
    """
    _backfill_goal_ids(records)
    _backfill_user_ids(records)
    needs_rewrite = _normalize_project_ids(records)
    needs_rewrite = _normalize_sim_user_ids(records) or needs_rewrite
    for record in records:
        record["plan"] = _normalize_plan(record["plan"])
    return records, needs_rewrite


def _read_jsonl(path: Path) -> list[dict]:
    """Every non-blank line as one JSON object, oldest first."""
    records: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    records.append(json.loads(text))
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"{path} line {line_no} is corrupted and can't be "
                        f"read as JSON ({e}). Restore from a backup or fix "
                        "that line by hand before continuing."
                    ) from e
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e
    return records


def _migrate_legacy_plans_array() -> list[dict] | None:
    """If data/plans.json (JSON array) still exists and plans.jsonl does
    not, load it, write plans.jsonl, and rename the array file to
    plans.json.bak. Returns the records, or None if there was nothing
    to migrate."""
    if PLANS_FILE.exists() or not LEGACY_PLANS_FILE.exists():
        return None
    try:
        with open(LEGACY_PLANS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{LEGACY_PLANS_FILE} is corrupted and can't be read as JSON "
            f"({e}). Restore it from a backup or fix it by hand before "
            "continuing."
        ) from e
    if not isinstance(records, list):
        raise RuntimeError(
            f"{LEGACY_PLANS_FILE} is not a JSON array of goal records."
        )
    _save_all(records)
    bak = LEGACY_PLANS_FILE.with_suffix(".json.bak")
    LEGACY_PLANS_FILE.replace(bak)
    return records


def _load_all() -> list[dict]:
    """Read every saved record from disk, normalizing legacy plan shapes.

    Prefers data/plans.jsonl. On first run after the JSONL switch, a
    leftover data/plans.json array is migrated automatically.

    Promotes legacy goal_id → project_id and rewrites plans.jsonl when
    any line still used the old key (Phase B wire rename).

    Returns an empty list if no history file exists yet.
    """
    migrated = _migrate_legacy_plans_array()
    if migrated is not None:
        records, needs_rewrite = _normalize_records(migrated)
        if needs_rewrite:
            _save_all(records)
        return records

    if not PLANS_FILE.exists():
        return []
    records, needs_rewrite = _normalize_records(_read_jsonl(PLANS_FILE))
    if needs_rewrite:
        _save_all(records)
    return records


def _save_all(records: list[dict]) -> None:
    """
    Write the full list of records back to disk as JSONL, creating
    data/ if needed.

    Writes to a temp file and renames it into place - a rename is atomic
    on POSIX filesystems (macOS/Linux), so a crash mid-write can never
    leave plans.jsonl half-written/corrupted; the old file stays intact
    until the new one is fully written.
    """
    ensure_data_dir()
    tmp_file = PLANS_FILE.with_suffix(".jsonl.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    tmp_file.replace(PLANS_FILE)


def _append_record(record: dict) -> None:
    """Append one record as a single JSONL line. Used by save_plan()
    when history only grows; stamp_map_focus() still rewrites via
    _save_all() because it mutates an existing line."""
    ensure_data_dir()
    with open(PLANS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_plan(
    goal: str,
    plan: dict,
    feedback: str | None = None,
    duration: str | None = None,
    completed: bool = False,
    cancelled: bool = False,
    goal_id: int | None = None,
    frozen_duration: dict | None = None,
    current_step: int = 0,
    sim_user_id: int | None = None,
    step_status: list[str] | None = None,
) -> dict:
    """
    Append a new goal+plan record to history and persist it to disk.

    `feedback` is the user's feedback (if any) that caused this plan to
    be created - i.e. what they said about the *previous* plan's
    "now" action, which led the agent to replan. None for a brand
    new goal that has no prior feedback yet.

    `duration` is the free-text span the user asked this plan to cover
    (e.g. "30 minutes", "this week"), if they gave one - see
    run_stage3(). Stored so the history shows what was
    actually asked for, not just what came back.

    `completed` marks the whole goal (not just one "now" step) as
    done - the user said so explicitly, rather than the agent guessing
    it from a missing next action.

    `cancelled` marks the whole goal as abandoned - a distinct terminal
    status from `completed`, not a lesser/failed version of it. This
    function doesn't enforce the two being mutually exclusive; that's
    `cancel_goal()`'s job (it refuses to cancel an already-
    completed goal), same division of responsibility as everywhere
    else in this file - persistence stores what it's given, decisions
    live in the caller.

    `goal_id` (parameter name kept this round) is the project's real
    identity, separate from its display text. Stored on disk as
    `project_id`. Pass the existing id to continue a project already in
    history; leave it None for a genuinely new one (minted here).
    Never invent an id - always get it from an existing record or this
    function's return value.

    There is no `user_id` parameter (unlike the project id): every record is
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

    `step_status` (added 2026-09-07) is a per-step "open"/"resolved"
    list, parallel-indexed to `plan.steps` - separate from
    `current_step` so that an Action being reported done never, by
    itself, means the Step it was attempted for is realized (see
    docs/planning-model.md). None for goals with no steps, or steps
    saved before this field existed; callers treat a
    missing/mismatched-length list as "every step still open" rather
    than requiring a migration. Callers that carry `current_step`
    forward unchanged across a replan/user-change/cancellation must
    carry this forward the same way, or a Step's resolved status would
    be silently lost.

    `sim_user_id` optionally links this project to a simulated user
    (id#N in the UI). None is the normal case until Projects
    assigns one. Like `project_id`, never invented by a caller - pass
    an id from save_user()/load_users(), or carry the existing
    record's own `sim_user_id` forward unchanged across a replan
    (same reasoning as `frozen_duration`). Distinct from stub
    `user_id` (= DEFAULT_USER_ID).

    Returns the record that was saved (useful for confirming to the user).
    """
    records = _load_all()
    record = {
        "id": len(records) + 1,
        "user_id": DEFAULT_USER_ID,
        "project_id": goal_id if goal_id is not None else _next_goal_id(records),
        "sim_user_id": sim_user_id,
        "goal": goal,
        "plan": plan,
        "feedback": feedback,
        "duration": duration,
        "frozen_duration": frozen_duration,
        "current_step": current_step,
        "step_status": step_status,
        "completed": completed,
        "cancelled": cancelled,
        # Local time, naive (no tzinfo) - matches every other timestamp
        # in this project. Older records stored this in UTC; see
        # resolver.created_at_key() for sorting mixed-era history.
        "created_at": datetime.now().isoformat(),
    }
    records.append(record)
    _append_record(record)
    return record


def stamp_map_focus(
    goal_id: int,
    map_focus: str,
    focus_step_id: str | None = None,
) -> dict | None:
    """Attach map_focus (and optional step id) to the latest history
    record for this project — so the chat thread can frame 'about this
    node' and re-select it from the frame. Returns that record, or
    None if none found. Parameter name goal_id kept this round; matches
    project_id on disk.
    """
    label = (map_focus or "").strip()
    if not label:
        return None
    records = _load_all()
    for i in range(len(records) - 1, -1, -1):
        if record_project_id(records[i]) == goal_id:
            records[i]["map_focus"] = label
            step = (focus_step_id or "").strip()
            if step:
                records[i]["focus_step_id"] = step
            else:
                records[i].pop("focus_step_id", None)
            _save_all(records)
            return records[i]
    return None


def set_project_name(goal_id: int, name: str) -> dict | None:
    """Replace the display label on the latest record for this
    project. Identity is `project_id`; the `goal` field is only the
    name. Mutates in place (same as stamp_map_focus) so a rename is
    not a new chat turn. Parameter name goal_id kept this round.
    """
    label = (name or "").strip()
    if not label:
        return None
    records = _load_all()
    for i in range(len(records) - 1, -1, -1):
        if record_project_id(records[i]) == goal_id:
            if records[i].get("goal") == label:
                return records[i]
            records[i]["goal"] = label
            _save_all(records)
            return records[i]
    return None


def load_history() -> list[dict]:
    """Return every saved goal+plan record, oldest first."""
    return _load_all()


def get_latest_plan() -> dict | None:
    """Return the most recently saved record, or None if there's no history yet."""
    records = _load_all()
    return records[-1] if records else None


# ============================================================
# 3. Simulated users (users.json)
# ============================================================


def _load_all_users() -> list[dict]:
    """Read every saved simulated user. Empty list if neither users.json
    nor legacy visions.json exists. When only visions.json is present,
    load it and rewrite as users.json (one-shot promote).
    """
    if USERS_FILE.exists():
        path = USERS_FILE
    elif LEGACY_VISIONS_FILE.exists():
        path = LEGACY_VISIONS_FILE
    else:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            users = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e
    if path is LEGACY_VISIONS_FILE:
        _save_all_users(users)
    return users


def _save_all_users(users: list[dict]) -> None:
    """Write the full list of simulated users - same atomic-rename as
    _save_all()."""
    ensure_data_dir()
    tmp_file = USERS_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    tmp_file.replace(USERS_FILE)


def _next_user_id(users: list[dict]) -> int:
    """One higher than the largest user id, or 1 if none yet."""
    existing = [u["id"] for u in users]
    return max(existing, default=0) + 1


def save_user(text: str) -> dict:
    """
    Create a simulated user and persist it - a tenant slot projects can
    optionally reference via sim_user_id (see save_plan()).

    No history, no revisions: a single mutable fact, not a chain.
    Editing/deleting is intentionally not built yet - this only ever
    appends a new one.

    Returns the record that was saved.
    """
    users = _load_all_users()
    record = {
        "id": _next_user_id(users),
        "user_id": DEFAULT_USER_ID,
        "text": text,
        "created_at": datetime.now().isoformat(),
    }
    users.append(record)
    _save_all_users(users)
    return record


def load_users() -> list[dict]:
    """Return every saved simulated user, oldest first."""
    return _load_all_users()


def get_user(sim_user_id: int) -> dict | None:
    """Return the simulated user with this id, or None if missing."""
    for user in _load_all_users():
        if user["id"] == sim_user_id:
            return user
    return None


def archive_user(sim_user_id: int) -> dict | None:
    """
    Mark a simulated user as archived. Mutates the existing record in
    place. Returns the record, or None if id doesn't resolve. Archiving
    an already-archived user is a no-op.

    Never touches plans.jsonl - a project's sim_user_id is left as-is.
    """
    users = _load_all_users()
    for user in users:
        if user["id"] == sim_user_id:
            if user.get("archived"):
                return user
            user["archived"] = True
            _save_all_users(users)
            return user
    return None
