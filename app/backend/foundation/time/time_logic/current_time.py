"""The authoritative current-time source for backend - re-exported as
backend.foundation.time.time_logic.now (and, from there, as
backend.foundation.time.now)."""

from datetime import datetime


def now() -> datetime:
    """
    The current local date and time - the one place backend code reads
    the system clock, so every caller shares the same notion of "now"
    and a later extension (timezone, a frozen/mocked clock for tests,
    etc.) only has to happen here instead of at every call site. Naive/
    local, same datetime model the rest of this project already uses.
    """
    return datetime.now()
