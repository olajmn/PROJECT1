"""
Voice - the shared role that talks to the user.

Formerly LLM1 / `backend/llm1/interface.py`. Handed either the user's
own message with nothing yet to report, or a single, already plain-text
surface string a capability produced - never a capability's own
internal field names or data shape (see docs/v4-migration-decision.md,
"LLM1 must not need to know... PLAN_KEYS, step_status,
suggested_action, current_step"). Producing that plain-text string from
a capability's raw result is the calling harness's job, not Voice's or
the capability's - see cli.py / manifestation.surface_text().
"""

from backend.model.client import send_message

SYSTEM_PROMPT = (
    "You are a warm, direct personal assistant talking with the user in "
    "an ongoing conversation. You will be given the user's own message, "
    "and sometimes also a short update from the system about what "
    "happened as a result - if given, relay it naturally, in your own "
    "words, as part of your reply, rather than repeating it verbatim. "
    "Keep your reply to one or two short sentences. Never invent "
    "information beyond what you were given. If the update is a "
    "question or a concrete proposal, deliver that - do not dodge with "
    "praise like 'great question' or ask them to restate what they "
    "just asked you to suggest."
)


def respond(user_message: str, system_update: str | None) -> str:
    """One natural-language reply to `user_message`, optionally
    incorporating `system_update` - a plain-text string only."""
    user_content = f"The user said: {user_message}"
    if system_update:
        user_content += f"\n\nUpdate from the system to relay: {system_update}"
    return send_message(SYSTEM_PROMPT, user_content).strip()
