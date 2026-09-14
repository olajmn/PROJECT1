"""
Hypothesis - second module in module_library. Given a piece of text,
generates several distinct, plausible explanations or possibilities -
without picking, ranking, or evaluating any of them. That judgment
belongs elsewhere - this file has no knowledge of what "elsewhere"
is; it only ever sees whatever text and context it is called with.
"""

import json

from backend.model.client import send_message

SYSTEM_PROMPT = (
    "You generate hypotheses for one piece of text, given the purpose "
    "it is being read for, and optionally some additional context. A "
    "hypothesis is a plausible explanation or possibility - not a "
    "fact, and not something you are asserting is true. Generate "
    "several distinct hypotheses covering genuinely different "
    "angles, not variations on the same idea. Every hypothesis must "
    "be traceable to what you were given - do not invent one with no "
    "basis in it. Do not rank, compare, or pick a best hypothesis; do "
    "not evaluate any of them for weaknesses. Respond with ONLY a "
    "JSON object with exactly one key, \"hypotheses\", a JSON array "
    "of short strings."
)


def hypothesize(text: str, purpose: str, context: str | None = None) -> dict:
    """
    {"hypotheses": [<str>, ...]} for `text`, read for `purpose` -
    `context` optional (see module docstring). Falls back to an empty
    list if the model's response doesn't have the expected shape -
    never invents a fallback hypothesis.
    """
    user_content = f"Purpose: {purpose}\n\nText: {text}"
    if context:
        user_content += f"\n\nAdditional context: {context}"

    raw = send_message(SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    hypotheses = data.get("hypotheses")
    if not isinstance(hypotheses, list) or not all(isinstance(h, str) for h in hypotheses):
        hypotheses = []

    return {"hypotheses": hypotheses}
