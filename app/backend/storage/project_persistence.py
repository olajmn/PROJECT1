"""
Project persistence: current.json (SoT for map/chat) + events.jsonl
(slim change tape for Status/Logs) under data/projects/{id}/.

Legacy combined projects.jsonl / plans.jsonl / plans.json, and snapshot
{id}.jsonl files, migrate into this folder shape on first load.

Identity grouping for display lives in create/resolver.py — project_id
minting and on-load promotes stay here. Simulated users (id#N) live in
users_persistence.py and are only referenced via optional sim_user_id.
"""

# Contents
#  1. Paths & legacy normalization
#      - PROJECTS_DIR / LEGACY_* 
#      - project_dir() / current_path() / events_path()
#      - _normalize_plan() / record_project_id() / …
#  2. Project records (current.json + events.jsonl)
#      - load_current() / load_project_events() / save_plan()
#      - stamp_map_focus() / surface_from_plan()
#      - load_history() / load_all_currents()

import json
from datetime import datetime
from pathlib import Path

from backend.storage.paths import DATA_DIR, DEFAULT_USER_ID, ensure_data_dir, now_utc

PROJECTS_DIR = DATA_DIR / "projects"
# Older combined files — split into PROJECTS_DIR on first load.
LEGACY_PROJECTS_JSONL = DATA_DIR / "projects.jsonl"
LEGACY_PLANS_JSONL = DATA_DIR / "plans.jsonl"
LEGACY_PLANS_FILE = DATA_DIR / "plans.json"


# ============================================================
# 1. Paths & legacy normalization
# ============================================================


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


# ============================================================
# 2. Project records (data/projects/{id}/current.json + events.jsonl)
# ============================================================
#
# Current is the source of truth for map/chat. Events are a slim change
# tape for Status/Logs. Each save updates current and appends one event
# (no full map on the tape). Legacy data/projects/{id}.jsonl snapshot
# files migrate into the folder shape on first load.


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
        if "plan" in record:
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


def project_dir(project_id: int) -> Path:
    """data/projects/{id}/ — current + events for one project."""
    return PROJECTS_DIR / str(int(project_id))


def current_path(project_id: int) -> Path:
    return project_dir(project_id) / "current.json"


def events_path(project_id: int) -> Path:
    return project_dir(project_id) / "events.jsonl"


def project_path(project_id: int) -> Path:
    """Directory for one project (current.json + events.jsonl)."""
    return project_dir(project_id)


def _legacy_snapshot_path(project_id: int) -> Path:
    """Old single-file tape: data/projects/{id}.jsonl."""
    return PROJECTS_DIR / f"{int(project_id)}.jsonl"


def surface_from_plan(name: str, plan: dict | None) -> str:
    """One-line map summary for chat without storing the full tree."""
    progression = (plan or {}).get("progression") if isinstance(plan, dict) else None
    steps = progression.get("steps") if isinstance(progression, dict) else None
    if not isinstance(steps, list):
        return "The map is empty."
    labels = [
        (step.get("label") or "").strip()
        for step in steps
        if isinstance(step, dict) and (step.get("label") or "").strip()
    ]
    if not labels:
        return "The map is empty."
    listed = ", ".join(labels)
    label = (name or "").strip()
    return f"{label}: {listed}." if label else f"{listed}."


def _slim_event(record: dict) -> dict:
    """Drop the full map from a history line; keep tape fields."""
    event: dict = {
        "id": record.get("id"),
        "project_id": record_project_id(record),
        "user_id": record.get("user_id", DEFAULT_USER_ID),
        "created_at": record.get("created_at"),
    }
    for key in (
        "event", "feedback", "sent_at", "map_focus", "focus_step_id",
        "name", "sim_user_id", "surface", "completed", "cancelled",
        "archived_at",
    ):
        if key in record and record[key] is not None:
            event[key] = record[key]
    if "surface" not in event and "plan" in record:
        event["surface"] = surface_from_plan(
            record.get("name") or "", record.get("plan"),
        )
    return event


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} is not a JSON object.")
    return data


def _write_events(project_id: int, events: list[dict]) -> None:
    path = events_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    tmp.replace(path)


def _append_event(project_id: int, event: dict) -> None:
    path = events_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _write_project_store(project_id: int, records: list[dict]) -> None:
    """Write current + slim events from full snapshot lines (migration)."""
    if not records:
        return
    records, _ = _normalize_records(list(records))
    current = dict(records[-1])
    events = [_slim_event(r) for r in records]
    _write_json(current_path(project_id), current)
    _write_events(project_id, events)


def _project_store_exists(project_id: int) -> bool:
    return current_path(project_id).exists()


def _legacy_snapshot_files() -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    return [
        p for p in PROJECTS_DIR.iterdir()
        if p.is_file() and p.suffix == ".jsonl" and p.stem.isdigit()
    ]


def _project_files_exist() -> bool:
    """True when any per-project store (folder or legacy jsonl) exists."""
    if not PROJECTS_DIR.exists():
        return False
    if _legacy_snapshot_files():
        return True
    return any(
        p.is_dir() and p.name.isdigit() and (p / "current.json").exists()
        for p in PROJECTS_DIR.iterdir()
    )


def _migrate_legacy_snapshot_file(path: Path) -> None:
    """data/projects/{id}.jsonl → {id}/current.json + events.jsonl."""
    pid = int(path.stem)
    if _project_store_exists(pid):
        path.replace(_bak_path(path))
        return
    records = _read_jsonl(path)
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
        pid = record_project_id(record)
        if pid is None:
            continue
        by_id.setdefault(pid, []).append(record)
    for pid, lines in by_id.items():
        _write_project_store(pid, lines)


def _ensure_migrated() -> None:
    """Split a leftover combined jsonl/array once; then promote snapshot
    files into current+events folders."""
    if not _project_files_exist():
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

        if source is not None and records is not None:
            records, _ = _normalize_records(records)
            _write_split(records)
            source.replace(_bak_path(source))

    _ensure_folder_stores()


def _existing_project_ids() -> list[int]:
    """Numeric project ids that have a current.json (after migration)."""
    _ensure_migrated()
    if not PROJECTS_DIR.exists():
        return []
    ids: list[int] = []
    for path in PROJECTS_DIR.iterdir():
        if path.is_dir() and path.name.isdigit() and (path / "current.json").exists():
            ids.append(int(path.name))
    return ids


def _next_goal_id() -> int:
    """One higher than the largest project id on disk, or 1 if none.

    Name kept as _next_goal_id this round (Python symbol rename is a
    follow-up); values are project_id.
    """
    return max(_existing_project_ids(), default=0) + 1


def load_current(project_id: int) -> dict | None:
    """The project's current SoT record, or None."""
    _ensure_migrated()
    path = current_path(project_id)
    if not path.exists():
        return None
    record = _read_json(path)
    records, needs_rewrite = _normalize_records([record])
    current = records[0]
    if needs_rewrite:
        _write_json(path, current)
    return current


def load_project_events(project_id: int) -> list[dict]:
    """Slim change tape for one project, oldest first."""
    _ensure_migrated()
    path = events_path(project_id)
    if not path.exists():
        return []
    events = _read_jsonl(path)
    for event in events:
        if "goal" in event and event.get("name") is None:
            event["name"] = event.pop("goal")
        elif "goal" in event:
            del event["goal"]
    return events


def load_project_history(project_id: int) -> list[dict]:
    """Compatibility alias: the events tape (Status/chat/timeline)."""
    return load_project_events(project_id)


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
    map_focus: str | None = None,
    focus_step_id: str | None = None,
) -> dict:
    """
    Update the project's current SoT and append one slim event.

    Callers still pass the full project fields; only current.json keeps
    the map. The events tape stores event/feedback/times (and a one-line
    map surface for chat), not a full plan copy.

    `map_focus` / `focus_step_id` mark this Talk turn as about a selected
    node (About frames + model history). They are not inherited from the
    previous current — pass them only when this save is focused.

    Returns the current record that was saved.
    """
    _ensure_migrated()
    pid = project_id if project_id is not None else _next_goal_id()
    existing_events = load_project_events(pid)
    record = {
        "id": len(existing_events) + 1,
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
    focus = (map_focus or "").strip()
    if focus:
        record["map_focus"] = focus
        step = (focus_step_id or "").strip()
        if step:
            record["focus_step_id"] = step

    record["surface"] = surface_from_plan(name, plan)
    _write_json(current_path(pid), record)
    _append_event(pid, _slim_event(record))
    return record


def stamp_map_focus(
    project_id: int,
    map_focus: str,
    focus_step_id: str | None = None,
) -> dict | None:
    """Attach map_focus on current *and* the matching events line.

    Prefer passing focus into save_plan for new Talk turns. This remains
    for callers that already saved and need to tag the latest line.
    """
    label = (map_focus or "").strip()
    if not label:
        return None
    latest = load_current(project_id)
    if latest is None:
        return None
    latest["map_focus"] = label
    step = (focus_step_id or "").strip()
    if step:
        latest["focus_step_id"] = step
    else:
        latest.pop("focus_step_id", None)
    _write_json(current_path(project_id), latest)
    _stamp_latest_event(project_id, latest.get("id"), label, step or None)
    return latest


def _stamp_latest_event(
    project_id: int,
    record_id: int | None,
    map_focus: str,
    focus_step_id: str | None,
) -> None:
    """Patch map_focus onto the events.jsonl line with this id."""
    if record_id is None:
        return
    path = events_path(project_id)
    if not path.exists():
        return
    events = _read_jsonl(path)
    changed = False
    for event in events:
        if event.get("id") != record_id:
            continue
        event["map_focus"] = map_focus
        if focus_step_id:
            event["focus_step_id"] = focus_step_id
        else:
            event.pop("focus_step_id", None)
        changed = True
        break
    if changed:
        _write_events(project_id, events)


def load_history() -> list[dict]:
    """Every project's events, oldest first within each project
    (projects ordered by id)."""
    _ensure_migrated()
    all_records: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        all_records.extend(load_project_events(pid))
    return all_records


def load_all_currents() -> list[dict]:
    """Current SoT record for every project."""
    _ensure_migrated()
    currents: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        current = load_current(pid)
        if current is not None:
            currents.append(current)
    return currents


def get_latest_plan() -> dict | None:
    """Most recently touched current across every project, or None."""
    records = load_all_currents()
    if not records:
        return None

    def _at(record: dict) -> datetime:
        raw = record.get("created_at") or ""
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.min
        if parsed.tzinfo is not None:
            return parsed.astimezone().replace(tzinfo=None)
        return parsed

    return max(records, key=_at)


