"""What acts on time data - recognizes phrases, resolves them, freezes
and compares durations. Reads the sibling data/ package; understands
nothing on its own without it.

now() is implemented in current_time.py and re-exported here so
existing `from backend.foundation.time.time_logic import now` imports
(and, transitively, `from backend.foundation.time import now`) keep
working unchanged."""

from backend.foundation.time.time_logic.current_time import now

__all__ = ["now"]
