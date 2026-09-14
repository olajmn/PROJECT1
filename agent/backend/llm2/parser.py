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
    raw = send_message(SYSTEM_PROMPT, message, json_mode=True)
    data = json.loads(raw)
    about = data.get("about")
    if not isinstance(about, str) or not about.strip():
        about = message
    return {"about": about}
