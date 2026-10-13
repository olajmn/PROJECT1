"""
Shared on-disk roots for storage.

Project records and accounts both live under DATA_DIR; each has
its own module (project_persistence / accounts_persistence). Paths and the
stub operator id live here so neither module needs the other for them
(project_persistence imports accounts_persistence only lazily, for the
per-account `account_n` high-water mark).
"""

from datetime import datetime, timezone
from pathlib import Path

from backend.storage import sandboxes

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# The only stub operator user_id that exists today (auth deferred).
# Not the simulated multi-user filter — that is account_id on projects.
DEFAULT_USER_ID = 1


def data_dir() -> Path:
    """data/, or the visitor's sandbox while a public-demo request runs
    (sandboxes.py)."""
    return sandboxes.current() or DATA_DIR


def ensure_data_dir() -> None:
    """Create data/ (or the sandbox) if it doesn't exist yet. Safe to
    call repeatedly."""
    data_dir().mkdir(exist_ok=True)


def now_utc() -> str:
    """The current time as text, in UTC with its offset
    ("2026-09-25T18:27:51.305+00:00"), so it means the same moment on any
    machine. Records saved before 2026-09-25 hold local time without an
    offset; resolver.created_at_key() reads both."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
