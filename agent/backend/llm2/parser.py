"""
LLM2 - Parser / Compiler (docs/v4-migration-decision.md).

Transforms the human conversation into a structured, capability-
agnostic understanding of what is being talked about. Deliberately
produces NO judgment about whether action is needed and NO capability
name - that decision belongs to LLM3, not here. An "actionable" flag
here would already be a hidden capability-adjacent judgment dressed up
as a neutral description, not a genuinely capability-agnostic one (see
docs/v4-migration-decision.md, "LLM2 must not produce capability-specific
concepts").
"""

import json

from backend.model.client import send_message

SYSTEM_PROMPT = (
    "You read one message from an ongoing conversation and describe, "
    "in one neutral sentence, what it is actually about. Do not decide "
    "what should happen next. Do not judge whether it requires any "
    "action or response. Do not name or imply any system capability. "
    "Just describe the content, capability-agnostically. Respond with "
    "ONLY a JSON object with exactly one key, \"about\", a short "
    "string."
)


def understand(message: str) -> dict:
    """{"about": <neutral description of what `message` concerns>} -
    the only thing LLM3 sees of this turn. Falls back to the raw
    message itself if the model's response doesn't have the expected
    shape - the turn is never silently dropped."""
    return _about(SYSTEM_PROMPT, message, fallback=message)


CONTEXT_SYSTEM_PROMPT = (
    "You read one message from an ongoing conversation, together with "
    "a short setting that says what was already being talked about. "
    "Describe, in one neutral sentence, what the message is actually "
    "about in that setting. Do not decide what should happen next. "
    "Do not judge whether it requires any action or response. Do not "
    "name or imply any system capability. Respond with ONLY a JSON "
    "object with exactly one key, \"about\", a short string."
)


def understand_in_context(message: str, setting: str) -> dict:
    """Same shape as understand(), but the message is read against a
    known setting (e.g. a pending question) rather than in isolation.
    Still produces no judgment and no capability name - see the module
    docstring. Falls back to the raw message on a bad response, same
    as understand()."""
    user_content = f"Setting: {setting}\n\nThe user said: {message}"
    return _about(CONTEXT_SYSTEM_PROMPT, user_content, fallback=message)


def _about(system_prompt: str, user_content: str, fallback: str) -> dict:
    try:
        raw = send_message(system_prompt, user_content, json_mode=True)
        data = json.loads(raw)
        about = data.get("about")
        if not isinstance(about, str) or not about.strip():
            about = fallback
    except (json.JSONDecodeError, TypeError):
        about = fallback
    return {"about": about}
