"""
Simulated users (id#N) — data/users.json (legacy visions.json promoted
on load).

Project current + events live in project_persistence.py. Shared roots
(DATA_DIR, now_utc, …) live in paths.py.

A simulated user is a plain {id, text, created_at} record — no history.
Projects may reference one via optional sim_user_id. Archiving mutates
the user record in place; detaching projects is a higher-level decision
(project_user.archive_user()).

Every record also carries a stub user_id (DEFAULT_USER_ID) — the
operator of this app, not the multi-user filter.
"""

# Contents
#  1. Simulated users (users.json)
#      - save_user() / load_users() / get_user() / archive_user()

import json

from backend.store.paths import (
    DATA_DIR,
    DEFAULT_USER_ID,
    ensure_data_dir,
    now_utc,
)

USERS_FILE = DATA_DIR / "users.json"
LEGACY_VISIONS_FILE = DATA_DIR / "visions.json"


# ============================================================
# 1. Simulated users (users.json)
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
    optionally reference via sim_user_id.

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

    Never touches project files - a project's sim_user_id is left as-is.
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
