"""
Shared on-disk roots for storage.

Project records and simulated users both live under DATA_DIR; each has
its own module (project_persistence / users_persistence). Paths and the
stub operator id live here so those modules do not import each other.
"""

from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# The only stub operator user_id that exists today (auth deferred).
# Not the simulated multi-user filter — that is sim_user_id on projects.
DEFAULT_USER_ID = 1


def ensure_data_dir() -> None:
    """Create data/ if it doesn't exist yet. Safe to call repeatedly."""
    DATA_DIR.mkdir(exist_ok=True)


def now_utc() -> str:
    """The current time as text, in UTC with its offset
    ("2026-09-25T18:27:51.305+00:00"), so it means the same moment on any
    machine. Records saved before 2026-09-25 hold local time without an
    offset; resolver.created_at_key() reads both."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
