"""
Accounts (account#N) — data/accounts.json.

Legacy promote on load: accounts.json ← users.json ← visions.json.

Project current + events live in project_persistence.py. Shared roots
(DATA_DIR, now_utc, …) live in paths.py.

An account is a plain {id, text, created_at} record — no history.
Projects may reference one via optional sim_user_id. Archiving mutates
the account record in place; detaching projects is a higher-level decision
(project_user.archive_account()). Sticky project mint high-water is
`account_n_hi` (see project_persistence._next_account_n()).

Every record also carries a stub user_id (DEFAULT_USER_ID) — the
operator of this app, not the multi-account filter.

Permanent delete leaves a tombstone ({id, user_id, deleted, deleted_at})
so an account id is never reused: closed projects keep their
sim_user_id, and a reused id would silently hand them to a new account.
Tombstones count toward the next id and are invisible to every other
function here.
"""

# Contents
#  1. Accounts (accounts.json)
#      - save_account() / load_accounts() / get_account() / rename_account()
#      - archive_account() / restore_account() / delete_account()
#      - account_n_hi() / note_account_n()  (sticky project mint high-water)

import json

from backend.storage.paths import (
    DATA_DIR,
    DEFAULT_USER_ID,
    ensure_data_dir,
    now_utc,
)

ACCOUNTS_FILE = DATA_DIR / "accounts.json"
LEGACY_USERS_FILE = DATA_DIR / "users.json"
LEGACY_VISIONS_FILE = DATA_DIR / "visions.json"


# ============================================================
# 1. Accounts (accounts.json)
# ============================================================


def _load_all_accounts() -> list[dict]:
    """Read every saved account.

    Prefer accounts.json. Else promote users.json or visions.json into
    accounts.json (one-shot).
    """
    if ACCOUNTS_FILE.exists():
        path = ACCOUNTS_FILE
    elif LEGACY_USERS_FILE.exists():
        path = LEGACY_USERS_FILE
    elif LEGACY_VISIONS_FILE.exists():
        path = LEGACY_VISIONS_FILE
    else:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            accounts = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} is corrupted and can't be read as JSON ({e}). "
            "It may have been interrupted mid-write. Restore it from a "
            "backup or fix it by hand before continuing."
        ) from e
    if path is not ACCOUNTS_FILE:
        _save_all_accounts(accounts)
        if path is LEGACY_USERS_FILE:
            LEGACY_USERS_FILE.replace(LEGACY_USERS_FILE.with_suffix(".json.bak"))
        elif path is LEGACY_VISIONS_FILE:
            LEGACY_VISIONS_FILE.replace(LEGACY_VISIONS_FILE.with_suffix(".json.bak"))
    return accounts


def _save_all_accounts(accounts: list[dict]) -> None:
    """Write the full list of accounts — atomic temp-file rename."""
    ensure_data_dir()
    tmp_file = ACCOUNTS_FILE.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    tmp_file.replace(ACCOUNTS_FILE)


def _live(accounts: list[dict]) -> list[dict]:
    """Accounts minus delete tombstones."""
    return [a for a in accounts if not a.get("deleted")]


def _next_account_id(accounts: list[dict]) -> int:
    """One higher than the largest account id ever issued (tombstones
    included), or 1 if none yet."""
    existing = [a["id"] for a in accounts]
    return max(existing, default=0) + 1


def save_account(text: str) -> dict:
    """
    Create an account and persist it — a tenant slot projects can
    optionally reference via sim_user_id.

    No history, no revisions: a single mutable fact, not a chain.

    Returns the record that was saved.
    """
    accounts = _load_all_accounts()
    record = {
        "id": _next_account_id(accounts),
        "user_id": DEFAULT_USER_ID,
        "text": text,
        "created_at": now_utc(),
    }
    accounts.append(record)
    _save_all_accounts(accounts)
    return record


def load_accounts() -> list[dict]:
    """Return every saved account, oldest first."""
    return _live(_load_all_accounts())


def get_account(sim_user_id: int) -> dict | None:
    """Return the account with this id, or None if missing."""
    for account in _live(_load_all_accounts()):
        if account["id"] == sim_user_id:
            return account
    return None


def rename_account(sim_user_id: int, text: str) -> dict | None:
    """
    Set the display label on an account. Empty / whitespace becomes
    the default "user" so the UI falls back to account#N. Returns the
    record, or None if id doesn't resolve. Archived accounts can still be
    renamed (label only).
    """
    label = (text or "").strip() or "user"
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == sim_user_id:
            account["text"] = label
            _save_all_accounts(accounts)
            return account
    return None


def account_n_hi(sim_user_id: int) -> int:
    """Highest sticky project mint ever issued for this account, or 0."""
    account = get_account(sim_user_id)
    if account is None:
        return 0
    hi = account.get("account_n_hi")
    return hi if isinstance(hi, int) else 0


def note_account_n(sim_user_id: int, n: int) -> None:
    """Raise account_n_hi so mints never reuse after delete or move-away."""
    if not isinstance(n, int) or n < 1:
        return
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == sim_user_id:
            prev = account.get("account_n_hi")
            prev = prev if isinstance(prev, int) else 0
            if n > prev:
                account["account_n_hi"] = n
                _save_all_accounts(accounts)
            return


def archive_account(sim_user_id: int) -> dict | None:
    """
    Mark an account as archived. Mutates the existing record in
    place. Returns the record, or None if id doesn't resolve. Archiving
    an already-archived account is a no-op.

    Never touches project files — a project's sim_user_id is left as-is.
    """
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == sim_user_id:
            if account.get("archived"):
                return account
            account["archived"] = True
            account["archived_at"] = now_utc()
            _save_all_accounts(accounts)
            return account
    return None


def restore_account(sim_user_id: int) -> dict | None:
    """Clear archived on an account. No-op if already live. None if missing."""
    accounts = _load_all_accounts()
    for account in _live(accounts):
        if account["id"] == sim_user_id:
            if not account.get("archived"):
                return account
            account.pop("archived", None)
            account.pop("archived_at", None)
            _save_all_accounts(accounts)
            return account
    return None


def delete_account(sim_user_id: int) -> dict | None:
    """Replace an account with a tombstone (see module docstring).
    Returns the record as it was before deletion, or None if id doesn't
    resolve. Does not touch project files."""
    accounts = _load_all_accounts()
    for i, account in enumerate(accounts):
        if account["id"] == sim_user_id and not account.get("deleted"):
            accounts[i] = {
                "id": account["id"],
                "user_id": account.get("user_id", DEFAULT_USER_ID),
                "deleted": True,
                "deleted_at": now_utc(),
            }
            _save_all_accounts(accounts)
            return account
    return None
