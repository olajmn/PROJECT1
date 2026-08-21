"""
Deterministic classification of free-text feedback into one of the
agent's four outcomes: "done", "not_done", "in_progress", "goal_done".

No LLM call - just recognized phrases, the same approach as
backend/timeperiod.py's resolve_duration() and for the same reason:
predictable, inspectable, and free of the hallucination/drift risk an
LLM classification call would carry for exactly the kind of true/false
decision this project has already been burned by trusting a model with
(see docs/11-experiments.md). Classifying "did you finish this?" from
free text is structurally the same kind of guess as the model
inventing a hallucinated detail - just one step earlier in the
pipeline - so it gets the same "recognize what you can name, admit what
you can't" treatment duration parsing already uses, not a model call.

The recognized phrases themselves (GOAL_DONE_PHRASES, etc.) live in
backend/outcome_phrases.py, not here - this file is the logic that
matches and classifies using them. Split apart 2026-08-21, same
data/logic separation as backend/timesegments.py vs backend/
timeperiod.py: the phrase lists are meant to grow over time as real
usage turns up new phrasings people actually type, without that growth
cluttering the matching logic that uses them.
"""

from __future__ import annotations

import re

from backend.outcome_phrases import RULES


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    True if `phrase` appears in `text` as whole word(s), not merely as
    a run of characters inside a longer, unrelated word. Plain
    substring containment would make "no" match inside "not"/"know"/
    "now" - \\b matches only at a boundary between a word character and
    a non-word one (or the string's start/end), so it correctly refuses
    those while still matching multi-word phrases like "did not" as a
    unit.
    """
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def classify_outcome(text: str) -> str | None:
    """
    Return one of "done", "not_done", "in_progress", "goal_done" if
    `text` confidently contains a recognized phrase (see
    backend/outcome_phrases.py's RULES), else None.

    None means "genuinely don't know" - callers must never treat it as
    a guessed default toward a risky outcome (done/goal_done); see
    backend/devtools/app.py's /feedback route, which falls back to the
    same safe no-op behavior as an explicit "in_progress" for anything
    unrecognized.
    """
    lowered = text.lower()
    for label, phrases in RULES:
        if any(_contains_phrase(lowered, phrase) for phrase in phrases):
            return label
    return None
