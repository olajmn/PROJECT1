"""
A project's lifecycle: mint one, abandon one, restore or erase.

Identity and current state stay in resolver.py - this module only
writes. Mint is create_project() — a name and an empty canvas, no
engine. Renaming the label is rename.py. Cancelling never does.
Vision is accepted here as an optional link at birth, but
linking/unlinking later stays on project_account.set_project_user()
until Vision's own shape is decided.
"""

# Contents
#  1. Creation
#      - create_project()
#      - next_default_name()
#
#  2. Cancellation / restore / delete
#      - cancel_project() / restore_project() / delete_project()

import re

from backend.storage.project_persistence import (
    delete_project as erase_project_store,
    save_plan,
)
from backend.project.panes.create.resolver import (
    get_latest_for_all_projects,
    get_latest_for_project,
)
from backend.storage.accounts_persistence import get_account


# ============================================================
# 1. Creation
# ============================================================


def create_project(typed_text: str, account_id_value: str) -> dict:
    """
    Mint a project: a name and an empty canvas. No engine.

    The typed text is only a label. The tree arrives afterwards —
    built by hand, pasted, or walked in from a folder. Empty text gets
    `next_default_name()`, so every client names the same way.
    """
    account_id = int(account_id_value) if account_id_value else None
    name = typed_text.strip() or next_default_name(account_id)
    return save_plan(
        name,
        {"progression": {"steps": []}},
        account_id=account_id,
        event="created",
    )


# Bare "New project" and legacy "New project #4" count too.
_DEFAULT_NAME_RE = re.compile(r"^new project(?: #?(\d+))?$", re.IGNORECASE)


def next_default_name(account_id: int | None) -> str:
    """
    Next unused `New project N` among this account's active projects.

    Counts per account, so each seat starts at 1; archived projects
    don't count, matching what the sidebar shows.
    """
    highest = 0
    for record in get_latest_for_all_projects():
        if record.get("account_id") != account_id:
            continue
        if record.get("completed") or record.get("cancelled"):
            continue
        match = _DEFAULT_NAME_RE.match((record.get("name") or "").strip())
        if match:
            highest = max(highest, int(match.group(1) or 1))
    return f"New project {highest + 1}"


# ============================================================
# 2. Cancellation / restore / delete
# ============================================================


def cancel_project(project_id: int) -> dict | None:
    """
    Mark a project as cancelled (abandoned) - a distinct terminal status
    from `completed`, not a UI-level relabeling of it and not a third
    planning decision. Preserves `plan` and `account_id` from the
    latest record exactly as they were, so the project's own data/history
    is never lost, only marked as no longer being pursued (still
    visible in full in the project's timeline, same as any other project).

    Returns the newly saved record, or None if the change is
    rejected - never partially applied:
    - `project_id` doesn't resolve to any project.
    - the project is already completed - a finished project doesn't also
      become abandoned; one terminal status wins, and completion,
      already decided, isn't overwritten by a later Cancel click.

    Requesting cancellation on an already-cancelled project is a genuine
    no-op - returns `latest` unchanged rather than appending an
    identical record (same idiom as set_project_user()).
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("completed"):
        return None
    if latest.get("cancelled"):
        return latest

    return save_plan(
        latest["name"], latest["plan"], feedback="Cancelled",
        project_id=latest["project_id"],
        account_id=latest.get("account_id"), cancelled=True,
        event="archived",
    )


def restore_project(project_id: int) -> dict | None:
    """Clear cancelled so the project is active again.

    No-op if already live. Returns None if missing or completed
    (completed is not restored this way). If its account was deleted in
    the meantime, the project comes back unassigned rather than tied to
    an account that no longer exists.
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("completed"):
        return None
    if not latest.get("cancelled"):
        return latest

    owner = latest.get("account_id")
    if owner is not None and get_account(owner) is None:
        owner = None

    return save_plan(
        latest["name"], latest["plan"], feedback="Restored",
        project_id=latest["project_id"],
        account_id=owner, cancelled=False,
        completed=False,
        event="restored",
    )


def delete_project(project_id: int) -> bool:
    """Permanently erase the project store. True if something was removed."""
    return erase_project_store(project_id)
