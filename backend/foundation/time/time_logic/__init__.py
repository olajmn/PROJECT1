"""What acts on time data - recognizes phrases, resolves them, freezes
and compares durations. Reads the sibling data/ package; understands
nothing on its own without it."""

from datetime import datetime


def now() -> datetime:
    """
    The current local date and time - the one place backend code reads
    the system clock, so every caller shares the same notion of "now"
    and a future change (timezone, a frozen/mocked clock for tests,
    etc.) only has to happen here instead of at every call site. Naive/
    local, same datetime model the rest of this project already uses
    (see docs/03-architecture.md § Time).
    """
    return datetime.now()
