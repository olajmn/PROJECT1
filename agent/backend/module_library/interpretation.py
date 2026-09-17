"""
Interpretation - first module in module_library. Distinguishes what a
piece of text explicitly states, what would only be an inference, and
which specific terms in it are themselves ambiguous - given the
purpose it is being read for.

Deliberately does not: decide what should happen next, resolve
ambiguity into a single guessed meaning, or know which Node - or which
other module - is calling it. `purpose` and `context` are plain
values supplied by the caller at call time; this module never
inspects their origin or assumes a particular shape behind them.
"""

import json

from backend.model.client import send_message

SYSTEM_PROMPT = (
    "You interpret one piece of text, given the purpose it is being "
    "read for, and optionally some additional context. Identify what "
    "is explicitly stated. Separately, list anything a reader would "
    "only be inferring, not something the text actually says. "
    "Preserve ambiguity rather than resolving it - do not guess a "
    "single meaning where more than one is plausible. Separately, "
    "identify any specific term or phrase in the text whose own "
    "meaning is unclear or could refer to more than one thing (e.g. "
    "a word like \"collapsed\" that could mean an economic, "
    "military, or political collapse) - for each one, give the term "
    "and its plausible meanings, without picking one. Do not decide "
    "what should happen next. Do not invent information beyond what "
    "is given. Respond with ONLY a JSON object with exactly three "
    "keys: \"explicit\", a string describing what is explicitly "
    "stated; \"inferred\", a JSON array of short strings, each one "
    "plausible inference - empty if none; and \"ambiguous_terms\", a "
    "JSON array of objects, each with \"term\" (the word or phrase) "
    "and \"meanings\" (a JSON array of its plausible meanings) - "
    "empty if none."
)


def interpret(text: str, purpose: str, context: str | None = None) -> dict:
    """
    {"explicit": <str>, "inferred": [<str>, ...], "ambiguous_terms":
    [{"term": <str>, "meanings": [<str>, ...]}, ...]} for `text`, read
    for `purpose` - `context` optional (see module docstring). Falls
    back to `text` itself as `explicit`, with no inferred items or
    ambiguous terms, if the model's response doesn't have the
    expected shape - the input is never silently dropped, same idiom
    as llm_roles.describe.describe().
    """
    user_content = f"Purpose: {purpose}\n\nText: {text}"
    if context:
        user_content += f"\n\nAdditional context: {context}"

    raw = send_message(SYSTEM_PROMPT, user_content, json_mode=True)
    data = json.loads(raw)

    explicit = data.get("explicit")
    if not isinstance(explicit, str) or not explicit.strip():
        explicit = text

    inferred = data.get("inferred")
    if not isinstance(inferred, list) or not all(isinstance(i, str) for i in inferred):
        inferred = []

    ambiguous_terms = data.get("ambiguous_terms")
    if not isinstance(ambiguous_terms, list) or not all(
        isinstance(t, dict)
        and isinstance(t.get("term"), str)
        and isinstance(t.get("meanings"), list)
        and all(isinstance(m, str) for m in t.get("meanings", []))
        for t in ambiguous_terms
    ):
        ambiguous_terms = []

    return {"explicit": explicit, "inferred": inferred, "ambiguous_terms": ambiguous_terms}
