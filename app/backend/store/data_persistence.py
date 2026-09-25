"""
Local storage for projects and simulated users (id#N). Project
history is one JSON object per line per project under
data/projects/{id}.jsonl (JSONL); simulated users are a JSON array in
data/users.json (legacy data/visions.json is promoted on first load).
Both git-ignored (see .gitignore) - this is personal information,
never committed.

A leftover combined data/projects.jsonl (or older plans.jsonl /
plans.json) is split into per-project files on first load; the
combined source is renamed *.bak.

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
#      - DATA_DIR / PROJECTS_DIR / LEGACY_* / USERS_FILE /
#        DEFAULT_USER_ID
#      - ensure_data_dir() / project_path()
#      - _LEGACY_HORIZON_KEY_RENAMES
#      - _normalize_plan()
#      - _backfill_goal_ids() / _normalize_project_ids() / record_project_id()
#      - _normalize_sim_user_ids()
#      - _backfill_user_ids()
#      - now_utc()
#
#  2. Project records (data/projects/{id}.jsonl)
#      - _ensure_migrated() / _next_goal_id()
#      - load_project_history() / _save_project() / _append_record()
#      - save_plan()  (persists project_id + sim_user_id)
#      - stamp_map_focus()
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
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROJECTS_DIR = DATA_DIR / "projects"
# Older combined files — split into PROJECTS_DIR on first load.
LEGACY_PROJECTS_JSONL = DATA_DIR / "projects.jsonl"
LEGACY_PLANS_JSONL = DATA_DIR / "plans.jsonl"
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


def project_path(project_id: int) -> Path:
    """data/projects/{id}.jsonl — that project's full history tape."""
    return PROJECTS_DIR / f"{int(project_id)}.jsonl"


def _ensure_projects_dir() -> None:
    ensure_data_dir()
    PROJECTS_DIR.mkdir(exist_ok=True)


# one_year/one_month/this_week/this_hour/this_minute/right_now renamed
# to year/month/week/hour/minute/now (leftover plan-record slots) once
# those turned out to name time levels, not literal durations or
# deictic phrases - existing saved records still have the old names.
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
    beyond their display text. Assign one id per distinct name, in
    first-appearance order, onto project_id (legacy files used goal_id;
    _normalize_project_ids promotes that).

    Records that already have project_id or goal_id are left untouched.
    Reads legacy `goal` or current `name` for the display text.
    """
    seen: dict[str, int] = {}
    next_id = 1
    for record in records:
        if record.get("project_id") or record.get("goal_id"):
            continue
        text = record.get("name") or record.get("goal") or ""
        if text not in seen:
            seen[text] = next_id
            next_id += 1
        record["project_id"] = seen[text]


def _normalize_project_ids(records: list[dict]) -> bool:
    """Promote legacy goal_id → project_id; drop goal_id from memory.

    Returns True if any record still had only goal_id on disk shape
    (caller should rewrite that project's file so grepping shows
    project_id).
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


def _normalize_project_names(records: list[dict]) -> bool:
    """Promote legacy goal → name; drop goal from memory.

    Returns True if a disk rewrite is needed so grepping shows name.
    """
    needed_rewrite = False
    for record in records:
        if "goal" in record:
            if record.get("name") is None:
                record["name"] = record["goal"]
            del record["goal"]
            needed_rewrite = True
        elif "name" not in record:
            record["name"] = ""
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


def now_utc() -> str:
    """The current time as text, in UTC with its offset
    ("2026-09-25T18:27:51.305+00:00"), so it means the same moment on any
    machine. Records saved before 2026-09-25 hold local time without an
    offset; resolver.created_at_key() reads both."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ============================================================
# 2. Project records (data/projects/{id}.jsonl)
# ============================================================


def _normalize_records(records: list[dict]) -> tuple[list[dict], bool]:
    """Backfill ids and normalize plan shapes in place.

    Returns (records, needs_disk_rewrite) — rewrite when goal_id was
    promoted to project_id, vision_id to sim_user_id, or goal to name.
    """
    _backfill_goal_ids(records)
    _backfill_user_ids(records)
    needs_rewrite = _normalize_project_ids(records)
    needs_rewrite = _normalize_sim_user_ids(records) or needs_rewrite
    needs_rewrite = _normalize_project_names(records) or needs_rewrite
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


def _bak_path(path: Path) -> Path:
    """Sibling backup name: foo.jsonl → foo.jsonl.bak."""
    return path.parent / (path.name + ".bak")


def _project_files_exist() -> bool:
    if not PROJECTS_DIR.exists():
        return False
    return any(
        p.suffix == ".jsonl" and p.stem.isdigit()
        for p in PROJECTS_DIR.iterdir()
    )


def _read_legacy_array(path: Path) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} is corrupted and can't be read as JSON ({e}). "
            "Restore it from a backup or fix it by hand before continuing."
        ) from e
    if not isinstance(records, list):
        raise RuntimeError(
            f"{path} is not a JSON array of goal records."
        )
    return records


def _write_split(records: list[dict]) -> None:
    """Write records into data/projects/{id}.jsonl, grouped by project_id."""
    by_id: dict[int, list[dict]] = {}
    for record in records:
        pid = record_project_id(record)
        if pid is None:
            continue
        by_id.setdefault(pid, []).append(record)
    for pid, lines in by_id.items():
        _save_project(pid, lines)


def _ensure_migrated() -> None:
    """If per-project files already exist, do nothing. Otherwise split a
    leftover combined projects.jsonl / plans.jsonl / plans.json once."""
    if _project_files_exist():
        return

    source: Path | None = None
    records: list[dict] | None = None
    if LEGACY_PROJECTS_JSONL.exists():
        source = LEGACY_PROJECTS_JSONL
        records = _read_jsonl(source)
    elif LEGACY_PLANS_JSONL.exists():
        source = LEGACY_PLANS_JSONL
        records = _read_jsonl(source)
    elif LEGACY_PLANS_FILE.exists():
        source = LEGACY_PLANS_FILE
        records = _read_legacy_array(source)

    if source is None or records is None:
        return

    records, _ = _normalize_records(records)
    _write_split(records)
    source.replace(_bak_path(source))


def _existing_project_ids() -> list[int]:
    """Numeric stems of data/projects/*.jsonl after migration."""
    _ensure_migrated()
    if not PROJECTS_DIR.exists():
        return []
    ids: list[int] = []
    for path in PROJECTS_DIR.iterdir():
        if path.suffix != ".jsonl" or not path.stem.isdigit():
            continue
        ids.append(int(path.stem))
    return ids


def _next_goal_id() -> int:
    """One higher than the largest project id on disk, or 1 if none.

    Name kept as _next_goal_id this round (Python symbol rename is a
    follow-up); values are project_id.
    """
    return max(_existing_project_ids(), default=0) + 1


def _save_project(project_id: int, records: list[dict]) -> None:
    """Atomic rewrite of one project's JSONL file."""
    _ensure_projects_dir()
    path = project_path(project_id)
    tmp_file = path.with_suffix(".jsonl.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    tmp_file.replace(path)


def _append_record(record: dict) -> None:
    """Append one record to that project's JSONL file."""
    pid = record_project_id(record)
    if pid is None:
        raise RuntimeError("Cannot append a history line without project_id.")
    _ensure_projects_dir()
    path = project_path(pid)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_project_history(project_id: int) -> list[dict]:
    """Every saved line for one project, oldest first. Empty if none."""
    _ensure_migrated()
    path = project_path(project_id)
    if not path.exists():
        return []
    records, needs_rewrite = _normalize_records(_read_jsonl(path))
    if needs_rewrite:
        _save_project(project_id, records)
    return records


def _load_all() -> list[dict]:
    """Every project's lines, ordered by project_id then file order.

    Runs one-shot migration from a combined jsonl/array if needed.
    Promotes legacy goal_id → project_id / vision_id → sim_user_id and
    rewrites that project's file when any line still used the old key.
    """
    _ensure_migrated()
    if not PROJECTS_DIR.exists():
        return []
    all_records: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        all_records.extend(load_project_history(pid))
    return all_records


def save_plan(
    name: str,
    plan: dict,
    feedback: str | None = None,
    duration: str | None = None,
    completed: bool = False,
    cancelled: bool = False,
    project_id: int | None = None,
    frozen_duration: dict | None = None,
    current_step: int = 0,
    sim_user_id: int | None = None,
    step_status: list[str] | None = None,
    event: str | None = None,
    sent_at: str | None = None,
) -> dict:
    """
    Append a new project record to history and persist it to disk.

    `feedback` is the user's feedback (if any) that caused this plan to
    be created - i.e. what they said about the *previous* plan's
    "now" action, which led the agent to replan. None for a brand
    new project that has no prior feedback yet.

    `duration` is a leftover stored span (e.g. "30 minutes"), if one
    was ever given. Chat and Create do not write a new one.

    `completed` marks the whole project (not just one "now" step) as
    done - the user said so explicitly, rather than the agent guessing
    it from a missing next action.

    `cancelled` marks the whole project as abandoned - a distinct terminal
    status from `completed`, not a lesser/failed version of it. This
    function doesn't enforce the two being mutually exclusive; that's
    `cancel_project()`'s job (it refuses to cancel an already-
    completed project), same division of responsibility as everywhere
    else in this file - persistence stores what it's given, decisions
    live in the caller.

    `project_id` is the project's real identity, separate from its
    display `name`. Pass the existing id to continue a project already
    in history; leave it None for a genuinely new one (minted here).
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
    docs/planning-model.md). None for projects with no steps, or steps
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

    `event` names what happened, for the project's timeline
    (project/timeline.py): "created", "chat", "node_added", "renamed", ...
    Records saved before 2026-09-25 have none; the timeline reads their
    `feedback` text instead.

    `sent_at` is when the user sent a chat message, which can be well
    before `created_at` (when the reply was saved). Chat turns only.

    Returns the record that was saved (useful for confirming to the user).
    """
    _ensure_migrated()
    pid = project_id if project_id is not None else _next_goal_id()
    existing = load_project_history(pid)
    record = {
        "id": len(existing) + 1,
        "user_id": DEFAULT_USER_ID,
        "project_id": pid,
        "sim_user_id": sim_user_id,
        "name": name,
        "plan": plan,
        "feedback": feedback,
        "duration": duration,
        "frozen_duration": frozen_duration,
        "current_step": current_step,
        "step_status": step_status,
        "completed": completed,
        "cancelled": cancelled,
        "created_at": now_utc(),
    }
    if event:
        record["event"] = event
    if sent_at:
        record["sent_at"] = sent_at
    _append_record(record)
    return record


def stamp_map_focus(
    project_id: int,
    map_focus: str,
    focus_step_id: str | None = None,
) -> dict | None:
    """Attach map_focus (and optional step id) to the latest history
    record for this project — so the chat thread can frame 'about this
    node' and re-select it from the frame. Returns that record, or
    None if none found.
    """
    label = (map_focus or "").strip()
    if not label:
        return None
    records = load_project_history(project_id)
    if not records:
        return None
    latest = records[-1]
    latest["map_focus"] = label
    step = (focus_step_id or "").strip()
    if step:
        latest["focus_step_id"] = step
    else:
        latest.pop("focus_step_id", None)
    _save_project(project_id, records)
    return latest


def load_history() -> list[dict]:
    """Return every saved goal+plan record across projects, oldest
    first within each project (projects ordered by id)."""
    return _load_all()


def get_latest_plan() -> dict | None:
    """Return the most recently saved record across every project, or
    None if there's no history yet."""
    records = _load_all()
    if not records:
        return None

    def _at(record: dict) -> datetime:
        raw = record.get("created_at") or ""
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.min
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    return max(records, key=_at)


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
    """Write the full list of simulated users - atomic temp-file rename."""
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
        "created_at": now_utc(),
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

    Never touches project history files - a project's sim_user_id is
    left as-is.
    """
    users = _load_all_users()
    for user in users:
        if user["id"] == sim_user_id:
            if user.get("archived"):
                return user
            user["archived"] = True
            user["archived_at"] = now_utc()
            _save_all_users(users)
            return user
    return None
