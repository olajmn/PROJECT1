"""
Project persistence: current.json (SoT for map/chat) + events.jsonl
(slim change tape for Status/Logs) under data/projects/{id}/.

Identity grouping for display lives in create/resolver.py — project_id
minting stays here. Simulated users (account#N) live in
accounts_persistence.py and are only referenced via optional account_id.
Per-account sticky mint `account_n` (map/chrome `#N`) is assigned here;
global `project_id` stays the wire identity.
"""

# Contents
#  1. Identity
#      - PROJECTS_DIR / record_project_id()
#  2. Project records (current.json + events.jsonl)
#      - project_dir() / current_path() / events_path()
#      - _slim_event()
#      - _next_project_id() / _next_account_n() / _resolve_account_n()
#      - load_current() / load_project_events() / save_plan()
#      - load_history() / load_all_currents() / delete_project()

import json
import shutil
from pathlib import Path

from backend.storage import sandboxes
from backend.storage.paths import DATA_DIR, DEFAULT_USER_ID, now_utc

PROJECTS_DIR = DATA_DIR / "projects"


# ============================================================
# 1. Identity
# ============================================================


def record_project_id(record: dict) -> int | None:
    """A history record's project id, or None when it has none."""
    pid = record.get("project_id")
    return int(pid) if pid is not None else None


# ============================================================
# 2. Project records (data/projects/{id}/current.json + events.jsonl)
# ============================================================
#
# Current is the source of truth for map/chat. Events are a slim change
# tape for Status/Logs. Each save updates current and appends one event
# (no full map on the tape).


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


def _projects_dir() -> Path:
    """PROJECTS_DIR, or projects/ in the visitor's demo sandbox."""
    sandbox = sandboxes.current()
    return sandbox / "projects" if sandbox else PROJECTS_DIR


def project_dir(project_id: int) -> Path:
    """data/projects/{id}/ — current + events for one project."""
    return _projects_dir() / str(int(project_id))


def current_path(project_id: int) -> Path:
    return project_dir(project_id) / "current.json"


def events_path(project_id: int) -> Path:
    return project_dir(project_id) / "events.jsonl"


def _slim_event(record: dict) -> dict:
    """Drop the full map from a history line; keep tape fields."""
    event: dict = {
        "id": record.get("id"),
        "project_id": record_project_id(record),
        "user_id": record.get("user_id", DEFAULT_USER_ID),
        "created_at": record.get("created_at"),
    }
    for key in (
        "event", "feedback", "sent_at", "map_focus", "focus_step_id", "focus_day",
        "name", "account_id", "completed", "cancelled",
        "archived_at",
    ):
        if key in record and record[key] is not None:
            event[key] = record[key]
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


def _iter_current_paths() -> list[tuple[int, Path]]:
    """(project_id, current.json path) for every on-disk project folder."""
    projects_dir = _projects_dir()
    if not projects_dir.exists():
        return []
    out: list[tuple[int, Path]] = []
    for path in projects_dir.iterdir():
        if path.is_dir() and path.name.isdigit():
            cur = path / "current.json"
            if cur.exists():
                out.append((int(path.name), cur))
    return out


def _existing_project_ids() -> list[int]:
    """Numeric project ids that have a current.json (after migration)."""
    return [pid for pid, _ in _iter_current_paths()]


def _next_project_id() -> int:
    """One higher than the largest project id on disk, or 1 if none."""
    return max(_existing_project_ids(), default=0) + 1


def _next_account_n(account_id: int) -> int:
    """Next sticky per-account mint (never reuses gaps after delete/move).

    Uses the account's account_n_hi high-water mark only — no full
    projects walk.
    """
    from backend.storage.accounts_persistence import account_n_hi, note_account_n

    n = account_n_hi(account_id) + 1
    note_account_n(account_id, n)
    return n


def _resolve_account_n(
    *,
    account_id: int | None,
    existing: dict | None,
) -> int | None:
    """Sticky account_n for this save.

    Keep the previous mint when the owner is unchanged. Mint a new one
    on create, claim, or move to another account. When unlinking, keep
    the historical mint on the record.
    """
    prev_n = existing.get("account_n") if existing else None
    prev_n = prev_n if isinstance(prev_n, int) else None
    if account_id is None:
        return prev_n
    prev_sim = existing.get("account_id") if existing else None
    if prev_n is not None and prev_sim == account_id:
        return prev_n
    return _next_account_n(account_id)


def _ensure_account_n(record: dict, path: Path) -> dict:
    """If this one record lacks account_n, mint and rewrite it.

    Only touches the project being loaded — no scan of siblings.
    """
    if record.get("account_n") is not None:
        return record
    sid = record.get("account_id")
    if not isinstance(sid, int):
        return record
    record["account_n"] = _next_account_n(sid)
    _write_json(path, record)
    return record


def load_current(project_id: int) -> dict | None:
    """The project's current SoT record, or None."""
    path = current_path(project_id)
    if not path.exists():
        return None
    return _ensure_account_n(_read_json(path), path)


def load_project_events(project_id: int) -> list[dict]:
    """Slim change tape for one project, oldest first."""
    path = events_path(project_id)
    if not path.exists():
        return []
    return _read_jsonl(path)


def load_project_history(project_id: int) -> list[dict]:
    """Compatibility alias: the events tape (Status/chat/timeline)."""
    return load_project_events(project_id)


def save_plan(
    name: str,
    plan: dict,
    feedback: str | None = None,
    completed: bool = False,
    cancelled: bool = False,
    project_id: int | None = None,
    account_id: int | None = None,
    event: str | None = None,
    sent_at: str | None = None,
    map_focus: str | None = None,
    focus_step_id: str | None = None,
    focus_day: str | None = None,
) -> dict:
    """
    Update the project's current SoT and append one slim event.

    Callers still pass the full project fields; only current.json keeps
    the map. The events tape stores event/feedback/times, not a full
    plan copy.

    `map_focus` / `focus_step_id` mark this chat turn as about a selected
    node (About frames + model history); `focus_step_id` alone marks a
    map edit on one node (a rename), for that node's chat. They are not
    inherited from the previous current — pass them only when this save
    is focused.
    `focus_day` (YYYY-MM-DD) marks a chat turn about one day's changes
    instead, the same way.

    Returns the current record that was saved.
    """
    pid = project_id if project_id is not None else _next_project_id()
    existing = load_current(pid) if project_id is not None else None
    account_n = _resolve_account_n(account_id=account_id, existing=existing)
    existing_events = load_project_events(pid)
    record = {
        "id": len(existing_events) + 1,
        "user_id": DEFAULT_USER_ID,
        "project_id": pid,
        "account_id": account_id,
        "account_n": account_n,
        "name": name,
        "plan": plan,
        "feedback": feedback,
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
    # Also on its own: a node rename names its node by id only.
    step = (focus_step_id or "").strip()
    if step:
        record["focus_step_id"] = step
    day = (focus_day or "").strip()
    if day:
        record["focus_day"] = day

    _write_json(current_path(pid), record)
    _append_event(pid, _slim_event(record))
    return record


def load_history() -> list[dict]:
    """Every project's events, oldest first within each project
    (projects ordered by id)."""
    all_records: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        all_records.extend(load_project_events(pid))
    return all_records


def load_all_currents() -> list[dict]:
    """Current SoT record for every project."""
    currents: list[dict] = []
    for pid in sorted(_existing_project_ids()):
        current = load_current(pid)
        if current is not None:
            currents.append(current)
    return currents


def delete_project(project_id: int) -> bool:
    """Permanently remove data/projects/{id}/ (current + events).

    Returns True if a store was removed, False if none existed.
    """
    path = project_dir(project_id)
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True
