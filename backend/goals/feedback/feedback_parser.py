"""
Parses the user's free-text feedback into machine-readable signals -
no LLM call, only explicit, named phrases:

    User feedback
          |
          v
    feedback_parser
          |
          v
    structured outcome / request

This exists because deciding "did the user finish this?" from
ambiguous free text is a guess a model could get wrong in exactly the
way this project has already been burned by (see
docs/06-development.md) - and because the answer directly drives what
the agent does next (replan, advance, mark complete). So the parser
only ever recognizes phrases it's been explicitly told about, and
admits it when it doesn't:

    Recognize what you can name. Admit what you can't.

Unrecognized text always returns None (outcome) or False (duration
request) - never a guess. Full change history: docs/06-development.md.
"""

from __future__ import annotations

import re


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    True if `phrase` appears in `text` as whole word(s), not merely as
    a run of characters inside a longer, unrelated word. Plain
    substring containment would make "no" match inside "not"/"know"/
    "now" - \\b matches only at a boundary between a word character and
    a non-word one (or the string's start/end), so it correctly refuses
    those while still matching multi-word phrases like "did not" as a
    unit. Not meant to be used outside this file - shared by both
    sections below.
    """
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


# ---------------------------------------------------------------------------
# OUTCOME PARSING
#
# What is the user telling us about the status of the action/goal?
# Answers one of: "goal_completed", "action_not_completed",
# "action_in_progress", "action_completed" - or None, genuinely
# unrecognized, never guessed.
# ---------------------------------------------------------------------------

# Checked in this order in parse_outcome() below - most specific /
# highest-stakes first. GOAL_COMPLETED permanently marks the whole
# goal complete (the hardest of the four to walk back), so it demands
# the most unambiguous phrasing and is checked before anything looser
# could steal the match.
GOAL_COMPLETED_PHRASES = (
    "goal complete",
    "goal is complete",
    "goal is done",
    "whole goal",
    "entire goal",
    "mark as complete",
    "mark complete",
    "mark the goal complete",
)

# ACTION_NOT_COMPLETED is checked before ACTION_COMPLETED because a
# negation like "didn't" contains "did" as a substring - checking
# ACTION_COMPLETED first would misfire on every negative sentence. "no"
# was added to this list 2026-08-20 (people fall back to old Yes/No
# button labels out of habit) - safe only because _contains_phrase()
# matches on word boundaries, not raw substring containment (a bare
# "no" would otherwise also match inside "not"/"know"/"now").
ACTION_NOT_COMPLETED_PHRASES = (
    "no",
    "nope",
    "nah",
    "didn't",
    "did not",
    "haven't",
    "have not",
    "not done",
    "not yet done",
    "couldn't",
    "could not",
    "failed to",
    "wasn't able",
    "was not able",
)

ACTION_IN_PROGRESS_PHRASES = (
    "still working",
    "in progress",
    "not yet",
    "working on it",
    "almost done",
    "not finished yet",
    "halfway",
    "in the middle of",
)

ACTION_COMPLETED_PHRASES = (
    "yes",
    "yeah",
    "yep",
    "yup",
    "done",
    "did it",
    "already did",
    "finished",
    "completed",
    "sent it",
    "sent them",
)


def parse_outcome(text: str) -> str | None:
    """
    Return one of "goal_completed", "action_not_completed",
    "action_in_progress", "action_completed" if `text` confidently
    contains a recognized phrase, else None.

    None means "genuinely don't know" - callers must never treat it as
    a guessed default toward a risky outcome (action_completed/
    goal_completed); see devtools/app.py's /feedback route, which
    falls back to the same safe no-op behavior as an explicit
    "action_in_progress" for anything unrecognized.

    Checked in a fixed order (see the phrase lists above) - the first
    match wins, so text that happens to contain phrases from more than
    one list still gets exactly one, unambiguous answer.
    """
    normalized_text = text.lower()

    if any(_contains_phrase(normalized_text, phrase) for phrase in GOAL_COMPLETED_PHRASES):
        return "goal_completed"

    if any(_contains_phrase(normalized_text, phrase) for phrase in ACTION_NOT_COMPLETED_PHRASES):
        return "action_not_completed"

    if any(_contains_phrase(normalized_text, phrase) for phrase in ACTION_IN_PROGRESS_PHRASES):
        return "action_in_progress"

    if any(_contains_phrase(normalized_text, phrase) for phrase in ACTION_COMPLETED_PHRASES):
        return "action_completed"

    return None


# ---------------------------------------------------------------------------
# DURATION CHANGE PARSING
#
# Is the user asking to change the goal's duration, instead of
# reporting progress? A different question entirely from OUTCOME
# PARSING above, not a fifth outcome - checked separately, and before,
# parse_outcome() in devtools/app.py's /feedback route.
# ---------------------------------------------------------------------------

# Replaces the old standalone "Extend timeframe" form - typing the
# request in the normal conversation box is the only way to do this
# now, so these phrases need to cover how someone would actually
# phrase that request, not a status report.
DURATION_CHANGE_PHRASES = (
    "change timeframe",
    "change the timeframe",
    "change time frame",
    "new timeframe",
    "different timeframe",
    "extend timeframe",
    "extend the timeframe",
    "extend the deadline",
    "change the deadline",
    "more time",
    "need more time",
)


def requests_duration_change(text: str) -> bool:
    """
    True if `text` is asking to change the goal's duration (e.g. "can
    we change timeframe", "I need more time") rather than reporting on
    progress. Checked separately from, and before, parse_outcome() in
    devtools/app.py's /feedback route - this isn't a fifth outcome,
    it's a different kind of message entirely, so it can't live in
    parse_outcome() without that function starting to return two
    unrelated kinds of answer from one call.

    Same deterministic, no-LLM approach as parse_outcome() above, for
    the same reason (see this module's docstring) - and the same
    honest limitation: only phrases in DURATION_CHANGE_PHRASES are
    recognized, so an unrecognized way of asking the same thing falls
    through to parse_outcome() instead (extend the phrase list as real
    phrasings turn up).
    """
    normalized_text = text.lower()
    return any(_contains_phrase(normalized_text, phrase) for phrase in DURATION_CHANGE_PHRASES)
