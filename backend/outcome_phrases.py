"""
Recognized feedback-phrase DATA only - no logic, no functions that
classify anything. Split out of outcome_classifier.py (2026-08-21),
same reasoning as backend/timesegments.py vs backend/timeperiod.py:
the phrase lists (what's recognized) are meant to grow over time as
real usage turns up new phrasings people actually type, and living in
their own file keeps that growth from cluttering the matching logic
that uses them (backend/outcome_classifier.py).

Nothing here does anything by itself - see outcome_classifier.py for
what turns these into an actual done/not_done/in_progress/goal_done
answer.
"""

# Checked in this order (see RULES) - most specific / highest-stakes
# first. GOAL_DONE permanently marks the whole goal complete (the
# hardest of the four to walk back), so it demands the most
# unambiguous phrasing and is checked before anything looser could
# steal the match. NOT_DONE is checked before DONE because a negation
# like "didn't" contains "did" as a substring - checking DONE first
# would misfire on every negative sentence.
#
# Every phrase is matched on word boundaries (see
# outcome_classifier.classify_outcome()), not raw substring containment
# - a bare "no" needed adding (2026-08-20; people fall back to the old
# Yes/No button labels out of habit), but "no" as
# a plain substring also sits inside "not", "know", "now" - a false
# positive on nearly any sentence containing one of those words.
# Word-boundary matching is what makes adding short, common words like
# "no"/"yes" safe to do at all.
GOAL_DONE_PHRASES = (
    "goal complete",
    "goal is complete",
    "goal is done",
    "whole goal",
    "entire goal",
    "mark as complete",
    "mark complete",
    "mark the goal complete",
)

NOT_DONE_PHRASES = (
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

IN_PROGRESS_PHRASES = (
    "still working",
    "in progress",
    "not yet",
    "working on it",
    "almost done",
    "not finished yet",
    "halfway",
    "in the middle of",
)

DONE_PHRASES = (
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

# (outcome label, phrases) in priority order - see the comment above
# for why this exact order matters. Extending this (a new phrase, a new
# outcome entirely) is a one-line change here; classify_outcome() in
# outcome_classifier.py never needs to know the specifics.
RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("goal_done", GOAL_DONE_PHRASES),
    ("not_done", NOT_DONE_PHRASES),
    ("in_progress", IN_PROGRESS_PHRASES),
    ("done", DONE_PHRASES),
)

# Separate from RULES above (2026-08-23) - this isn't a fifth outcome
# alongside done/not_done/in_progress/goal_done, it's a different kind
# of thing entirely: a request to change the goal's TIMEFRAME, checked
# by wants_duration_change() in outcome_classifier.py before outcome
# classification even runs (see backend/devtools/app.py's /feedback
# route). Replaces the old standalone "Extend timeframe" form - typing
# the request in the normal conversation box is the only way to do this
# now, so the phrases here need to cover how someone would actually
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
