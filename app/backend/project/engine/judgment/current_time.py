"""What time is it — for prompts.

Formats the real current moment as a string the model can read.
Does not parse user text about time (that lives in foundation/time).
"""

from backend.foundation.time import now


def current_time() -> str:
    """Grounds the model's «right now» in the real current moment."""
    return now().strftime("%A, %Y-%m-%d %H:%M")


# Older names.
now_str = current_time
_now_str = current_time
