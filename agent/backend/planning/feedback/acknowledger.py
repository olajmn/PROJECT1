"""
Generate a natural-language acknowledgment for feedback text that
feedback_parser.parse_outcome() couldn't classify - display only,
never a decision. Never told about outcomes, never allowed to
influence one: it only ever sees the raw note, and only ever returns
one sentence back, for the conversation thread.

Must never block or break the /feedback route: any failure (Ollama
not running, a timeout, an unexpected response) falls back to
FALLBACK_ACKNOWLEDGMENT - the same fixed text used before this
existed. A check-in must always succeed and save, with or without the
model.
"""

from backend.model.client import send_message

ACKNOWLEDGMENT_SYSTEM_PROMPT = (
    "You are acknowledging a short check-in note from someone working "
    "toward a goal. You don't know what it means well enough to act on "
    "it - write ONE short, warm sentence acknowledging you read it. "
    "Never guess whether they completed anything. Never mention a plan "
    "or next step. Respond with ONLY that one sentence, no other text."
)

FALLBACK_ACKNOWLEDGMENT = "Checked in (couldn't tell what this means yet)."


def acknowledge(note: str) -> str:
    """
    One short, model-generated sentence acknowledging `note`, or
    FALLBACK_ACKNOWLEDGMENT if the model call fails for any reason -
    see this module's docstring for why a failure here must never
    propagate to the caller.
    """
    try:
        reply = send_message(ACKNOWLEDGMENT_SYSTEM_PROMPT, note).strip()
        return reply or FALLBACK_ACKNOWLEDGMENT
    except Exception:
        return FALLBACK_ACKNOWLEDGMENT
