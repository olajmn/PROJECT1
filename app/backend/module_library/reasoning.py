"""
Reasoning - fourth module in module_library. Given a piece of text,
works out what actually follows from it and what remains genuinely
unresolved. Naming what's unresolved is part of drawing that
conclusion - not the same thing as the Planning capability's own job
of producing an executable plan (see planning/); this module never
produces one, and is not named after it, to avoid colliding with that
existing, unrelated concept. Has no knowledge of any other module - a
caller feeds whatever prior output it wants considered in as
`context`, in whatever words it chooses.
"""

import json

from backend.llm_client import send_message

SYSTEM_PROMPT = (
    "You reason about one piece of text, given the purpose it is "
    "being read for, and optionally some additional context. Work "
    "out what actually follows from everything you were given, and "
    "state a conclusion grounded only in that - never invent "
    "certainty it doesn't support. Separately, name what remains "
    "genuinely unresolved - a specific question or piece of "
    "information that would resolve it, not a vague gap. This is "
    "still analysis, not a plan: never describe steps to take or "
    "actions to perform. Respond with ONLY a JSON object with "
    "exactly two keys: \"conclusion\", a string; and "
    "\"open_questions\", a JSON array of short strings - empty if "
    "nothing remains unresolved."
)


def reason(text: str, purpose: str, context: str | None = None) -> dict:
    """
    {"conclusion": <str>, "open_questions": [<str>, ...]} for `text`,
    read for `purpose` - `context` optional (see module docstring).
    Falls back to `text` itself as `conclusion`, with no open
    questions, if the model's response doesn't have the expected
    shape.
    """
    user_content = f"Purpose: {purpose}\n\nText: {text}"
    if context:
        user_content += f"\n\nAdditional context: {context}"

    raw = send_message(SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    conclusion = data.get("conclusion")
    if not isinstance(conclusion, str) or not conclusion.strip():
        conclusion = text

    open_questions = data.get("open_questions")
    if not isinstance(open_questions, list) or not all(isinstance(q, str) for q in open_questions):
        open_questions = []

    return {"conclusion": conclusion, "open_questions": open_questions}
