"""
Session persistence — mint and list process-run records in
data/sessions.json.

Deliberately minimal: id, user_id, started_at, ended_at. What happened
during a Session is derived at read time (server.py's
_session_log_view()), not written here. See docs/04-current-state.md
§ 8.
"""

# Contents
#  1. File IO
#      - SESSIONS_FILE
#      - _load_all_sessions()
#      - _save_all_sessions()
#      - _next_session_id()
#
#  2. Public API
#      - start_session()
#      - load_sessions()

import json
from datetime import datetime

from backend.store.data_persistence import DATA_DIR, DEFAULT_USER_ID, ensure_data_dir

SESSIONS_FILE = DATA_DIR / "sessions.json"


# ============================================================
# 1. File IO
# ============================================================


def _load_all_sessions() -> list[dict]:
    """Read every saved Session from disk. Empty list if the file doesn't exist yet."""
    if not SESSIONS_FILE.exists():
        return []
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{SESSIONS_FILE} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e


def _save_all_sessions(sessions: list[dict]) -> None:
    """Write the full list of Sessions back to disk - same atomic-rename
    approach as data_persistence._save_all()."""
    ensure_data_dir()
    tmp_file = SESSIONS_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)
    tmp_file.replace(SESSIONS_FILE)


def _next_session_id(sessions: list[dict]) -> int:
    """One higher than the largest Session id in history, or 1 if there are none yet."""
    existing = [s["id"] for s in sessions]
    return max(existing, default=0) + 1


# ============================================================
# 2. Public API
# ============================================================


def start_session() -> dict:
    """
    Create a new Session record and persist it - called once per
    process (Session.__init__ in agent/process_turn.py, constructed
    once by cli.py's main() and once by server.py's module-level
    `session`), not once per request/turn.

    A Session here is deliberately minimal: just an id and when it
    started. It does not itself log what happened during it - that's
    derived at read time (server.py's _session_log_view()) from
    load_history()/load_visions(), both already timestamped, by
    filtering to whatever falls inside this Session's own
    [started_at, ended_at or now) window. See docs/04-current-state.md
    § 8 for why a session log is a read-time derivation, not a new
    write-path threaded through every mutating function.

    `ended_at` is always None here - nothing currently sets it (no
    graceful-shutdown hook exists yet), so a Session that is no longer
    actually running still shows as open indefinitely. A known,
    documented limitation (docs/04-current-state.md § 5), not an
    oversight - "closing" a session that was simply killed rather than
    exited cleanly isn't something this function can detect on its own.

    Returns the record that was saved.
    """
    sessions = _load_all_sessions()
    record = {
        "id": _next_session_id(sessions),
        "user_id": DEFAULT_USER_ID,
        "started_at": datetime.now().isoformat(),
        "ended_at": None,
    }
    sessions.append(record)
    _save_all_sessions(sessions)
    return record


def load_sessions() -> list[dict]:
    """Return every saved Session, oldest first."""
    return _load_all_sessions()
