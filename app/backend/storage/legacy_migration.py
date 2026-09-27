"""
Legacy migration — reading project data saved in formats older than
data/projects/{id}/current.json + events.jsonl.

Not part of the current model. project_persistence.py calls three entry
points, all no-ops on data already in the current shape:
- ensure_migrated(): converts leftover old files once — a combined
  projects.jsonl / plans.jsonl / plans.json, or a per-project snapshot
  {id}.jsonl — into the folder shape; each original is renamed *.bak.
- normalize_records(): on load, promotes old field names and shapes
  (goal_id → project_id, goal → name, vision_id → sim_user_id, a
  free-text plan, pre-rename horizon keys) and backfills ids.
- normalize_event(): the same `goal` → `name` promotion for a tape line.

Kept so an old backup can still be read; a 2026-09-27 audit found
nothing in data/ that needed it (docs/05-decisions.md #56). Uses the
current-format readers and writers from project_persistence.py.
"""

# Contents
#  1. Entry points
#      - ensure_migrated() / normalize_records() / normalize_event()
#  2. Old files → folder shape
#      - LEGACY_* / _write_split() / _migrate_legacy_snapshot_file() / …
#  3. Old fields and shapes
#      - _normalize_plan() / _backfill_goal_ids() / _normalize_project_ids() / …

import json
from pathlib import Path

from backend.storage import project_persistence as store
from backend.storage.paths import DATA_DIR, DEFAULT_USER_ID

# Older combined files — split into data/projects/ on first load.
LEGACY_PROJECTS_JSONL = DATA_DIR / "projects.jsonl"
LEGACY_PLANS_JSONL = DATA_DIR / "plans.jsonl"
LEGACY_PLANS_FILE = DATA_DIR / "plans.json"


# ============================================================
# 1. Entry points
# ============================================================


def ensure_migrated() -> None:
    """Split a leftover combined jsonl/array once; then promote snapshot
    files into current+events folders."""
    if not _project_files_exist():
        source: Path | None = None
        records: list[dict] | None = None
        if LEGACY_PROJECTS_JSONL.exists():
            source = LEGACY_PROJECTS_JSONL
            records = store._read_jsonl(source)
        elif LEGACY_PLANS_JSONL.exists():
            source = LEGACY_PLANS_JSONL
            records = store._read_jsonl(source)
        elif LEGACY_PLANS_FILE.exists():
            source = LEGACY_PLANS_FILE
            records = _read_legacy_array(source)

        if source is not None and records is not None:
            records, _ = normalize_records(records)
            _write_split(records)
            source.replace(_bak_path(source))

    _ensure_folder_stores()


def normalize_records(records: list[dict]) -> tuple[list[dict], bool]:
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
        if "plan" in record:
            record["plan"] = _normalize_plan(record["plan"])
    return records, needs_rewrite


def normalize_event(event: dict) -> dict:
    """Promote a tape line's legacy `goal` to `name`, in place."""
    if "goal" in event and event.get("name") is None:
        event["name"] = event.pop("goal")
    elif "goal" in event:
        del event["goal"]
    return event


# ============================================================
# 2. Old files → folder shape
# ============================================================


def _bak_path(path: Path) -> Path:
    """Sibling backup name: foo.jsonl → foo.jsonl.bak."""
    return path.parent / (path.name + ".bak")


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


def _legacy_snapshot_path(project_id: int) -> Path:
    """Old single-file tape: data/projects/{id}.jsonl."""
    return store.PROJECTS_DIR / f"{int(project_id)}.jsonl"


def _write_project_store(project_id: int, records: list[dict]) -> None:
    """Write current + slim events from full snapshot lines (migration)."""
    if not records:
        return
    records, _ = normalize_records(list(records))
    current = dict(records[-1])
    events = [store._slim_event(r) for r in records]
    store._write_json(store.current_path(project_id), current)
    store._write_events(project_id, events)


def _project_store_exists(project_id: int) -> bool:
    return store.current_path(project_id).exists()


def _legacy_snapshot_files() -> list[Path]:
    if not store.PROJECTS_DIR.exists():
        return []
    return [
        p for p in store.PROJECTS_DIR.iterdir()
        if p.is_file() and p.suffix == ".jsonl" and p.stem.isdigit()
    ]


def _project_files_exist() -> bool:
    """True when any per-project store (folder or legacy jsonl) exists."""
    if not store.PROJECTS_DIR.exists():
        return False
    if _legacy_snapshot_files():
        return True
    return any(
        p.is_dir() and p.name.isdigit() and (p / "current.json").exists()
        for p in store.PROJECTS_DIR.iterdir()
    )


def _migrate_legacy_snapshot_file(path: Path) -> None:
    """data/projects/{id}.jsonl → {id}/current.json + events.jsonl."""
    pid = int(path.stem)
    if _project_store_exists(pid):
        path.replace(_bak_path(path))
        return
    records = store._read_jsonl(path)
    if not records:
        path.replace(_bak_path(path))
        return
    _write_project_store(pid, records)
    path.replace(_bak_path(path))


def _ensure_folder_stores() -> None:
    """Promote any leftover snapshot jsonl files into current+events."""
    for path in list(_legacy_snapshot_files()):
        _migrate_legacy_snapshot_file(path)


def _write_split(records: list[dict]) -> None:
    """Write records into per-project current+events stores."""
    by_id: dict[int, list[dict]] = {}
    for record in records:
        pid = store.record_project_id(record)
        if pid is None:
            continue
        by_id.setdefault(pid, []).append(record)
    for pid, lines in by_id.items():
        _write_project_store(pid, lines)


# ============================================================
# 3. Old fields and shapes
# ============================================================


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
