"""
Link a project to an account#N, or archive an account and detach its projects.

Identity writes, not reasoning. Judgment does not own this.
"""

from backend.project.panes.create.resolver import (
    get_latest_for_all_projects,
    get_latest_for_project,
)
from backend.storage.accounts_persistence import (
    archive_account as archive_account_record,
    get_account,
)
from backend.storage.project_persistence import save_plan


def set_project_user(project_id: int, account_id: int | None) -> dict | None:
    """
    Add, move, or remove a project's account link after mint.
    `account_id=None` removes the project from whichever account it
    currently has.

    Unlike chat's talk() (which takes an already-resolved `latest`
    record), this resolves `project_id` itself, since the route calling
    it has no other reason to look the record up first.

    Returns the newly saved record, or None if the change is
    rejected - never partially applied, and never raises for an
    ordinary bad input:
    - `project_id` doesn't resolve to any goal.
    - `account_id` is given but no such account exists (a stale/tampered
      value - the real UI always offers ids from `load_accounts()`, so
      this is a defensive check, not the normal path).

    Requesting the account the project is already linked to (or already
    has none, for `account_id=None`) is a genuine no-op - returns
    `latest` unchanged rather than appending an identical record. A
    cancelled goal (see cancel_project()) is also a no-op here — never
    a save_plan() call that could silently revive it.

    Preserves `plan` and `completed` from the latest record exactly as
    they were -
    this changes which account the project belongs to, nothing about the
    map itself.
    """
    latest = get_latest_for_project(project_id)
    if latest is None:
        return None
    if latest.get("cancelled"):
        return latest

    previous_account_id = latest.get("account_id")
    if account_id == previous_account_id:
        return latest

    if account_id is None:
        feedback_text = "Removed from account"
    else:
        account = get_account(account_id)
        if account is None:
            return None
        verb = "Moved to" if previous_account_id is not None else "Added to"
        feedback_text = f"{verb} account: {account['text']}"

    return save_plan(
        latest["name"], latest["plan"], feedback=feedback_text,
        project_id=latest["project_id"],
        completed=latest.get("completed", False), account_id=account_id,
        event="owner_changed",
    )


def archive_account(account_id: int) -> dict | None:
    """
    Archive an account (accounts_persistence.archive_account()) and detach it
    from every currently-active project that references it - an archived
    account is no longer an active seat, so an active project
    shouldn't keep showing a current tie to it. Account and project have
    independent lifecycles: this never changes a project's plan or
    completed/cancelled status - only which account (if
    any) it currently points to.

    Completed/cancelled projects keep their account_id unchanged - already
    a closed, historical record, not a claim that the account is still
    active, so there's nothing to detach.

    Detaching reuses set_project_user(project_id, None) per project rather
    than writing a second way to change a project's account link, so it
    inherits that function's safety checks. Like set_project_user(),
    this appends a new record per affected project (project_id carried
    forward) - no existing record is ever mutated or removed.

    Returns the archived account record (or the already-archived one,
    unchanged, on a repeat call), or None if account_id doesn't exist.
    """
    account = archive_account_record(account_id)
    if account is None:
        return None

    for latest in get_latest_for_all_projects():
        if (latest.get("account_id") == account_id
                and not latest.get("completed")
                and not latest.get("cancelled")):
            set_project_user(latest["project_id"], None)

    return account
