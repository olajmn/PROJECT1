"""
Critique - third module in module_library. Given a piece of text,
identifies weaknesses, unsupported assumptions, or contradictions in
the claims it makes - one critique per thing it targets. Never
proposes a fix, never ranks or discards anything, never introduces a
new hypothesis of its own. Has no knowledge of where a claim came
from - if the caller wants specific possibilities critiqued, it passes
them in as `context`, in whatever words it chooses.
"""

import json

from backend.model.client import send_message

SYSTEM_PROMPT = (
    "You critique one piece of text, given the purpose it is being "
    "read for, and optionally some additional context - if that "
    "context lists specific claims or possibilities, critique each "
    "one individually; otherwise, critique the claims the text "
    "itself already makes. For each thing you critique, identify a "
    "concrete weakness: an unsupported assumption, missing evidence, "
    "an internal contradiction, or a plausible counterargument. Do "
    "not propose a fix or a better alternative. Do not rank, "
    "discard, or pick among the things you critique. Do not "
    "introduce a new hypothesis of your own. Respond with ONLY a "
    "JSON object with exactly one key, \"critiques\", a JSON array "
    "of objects, each with \"target\" (the claim or possibility "
    "being critiqued, as a short string) and \"weakness\" (the "
    "concrete weakness found)."
)


def critique(text: str, purpose: str, context: str | None = None) -> dict:
    """
    {"critiques": [{"target": <str>, "weakness": <str>}, ...]} for
    `text`, read for `purpose` - `context` optional (see module
    docstring). Falls back to an empty list if the model's response
    doesn't have the expected shape.
    """
    user_content = f"Purpose: {purpose}\n\nText: {text}"
    if context:
        user_content += f"\n\nAdditional context: {context}"

    raw = send_message(SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    critiques = data.get("critiques")
    if not isinstance(critiques, list) or not all(
        isinstance(c, dict) and isinstance(c.get("target"), str) and isinstance(c.get("weakness"), str)
        for c in critiques
    ):
        critiques = []

    return {"critiques": critiques}
