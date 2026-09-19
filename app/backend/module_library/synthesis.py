"""
Synthesis - fifth module in module_library. Given a piece of text,
produces the one result a Node actually acts on or shows - the only
module in this library whose output is meant to be consumed outside
module_library. Never states a claim that isn't traceable to what it
was given. Has no knowledge of any other module - a caller feeds
whatever it wants combined in as `context`, in whatever words it
chooses.
"""

import json

from backend.llm_client import send_message

SYSTEM_PROMPT = (
    "You synthesize one piece of text, given the purpose it is being "
    "read for, and optionally some additional context. Combine "
    "everything you were given into the single best, coherent result "
    "for that purpose - not a summary of each part in turn, but the "
    "answer it adds up to. Every claim in your result must be "
    "traceable to something you were given; never introduce a new "
    "fact or explanation of your own. If a genuine open question "
    "remains unresolved, say so plainly rather than resolving it by "
    "guessing. Respond with ONLY a JSON object with exactly one key, "
    "\"result\", a string."
)


def synthesize(text: str, purpose: str, context: str | None = None) -> dict:
    """
    {"result": <str>} for `text`, read for `purpose` - `context`
    optional (see module docstring). Falls back to `text` itself if
    the model's response doesn't have the expected shape - the input
    is never silently dropped.
    """
    user_content = f"Purpose: {purpose}\n\nText: {text}"
    if context:
        user_content += f"\n\nAdditional context: {context}"

    raw = send_message(SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    result = data.get("result")
    if not isinstance(result, str) or not result.strip():
        result = text

    return {"result": result}
