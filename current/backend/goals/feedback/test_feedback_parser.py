"""
Small, direct checks for feedback_parser.py's most important edge
cases - not a test framework, just asserts run top to bottom. Exists
to document intended behavior (especially the negation/word-boundary
safety), not to chase full coverage.

Run from the project root:
    .venv/bin/python -m backend.goals.feedback.test_feedback_parser
"""

from backend.goals.feedback.feedback_parser import (
    parse_outcome,
    requests_duration_change,
)

# (input text, expected parse_outcome() result)
OUTCOME_CASES = (
    ("yes", "action_completed"),
    ("did it", "action_completed"),
    ("no", "action_not_completed"),
    ("didn't do it", "action_not_completed"),
    ("still working", "action_in_progress"),
    ("goal is complete", "goal_completed"),
    # Word-boundary safety: "no" must match as its own word, but must
    # NOT fire just because it's a substring of an unrelated word.
    ("know", None),
    ("now", None),
    # Genuinely unrecognized text - never guessed toward an outcome.
    ("I sent 2 of 4 applications", None),
)

for text, expected in OUTCOME_CASES:
    actual = parse_outcome(text)
    assert actual == expected, f"parse_outcome({text!r}) = {actual!r}, expected {expected!r}"

# (input text, expected requests_duration_change() result)
DURATION_CASES = (
    ("need more time", True),
    ("can we change timeframe", True),
    ("still working", False),
    ("no", False),
)

for text, expected in DURATION_CASES:
    actual = requests_duration_change(text)
    assert actual == expected, f"requests_duration_change({text!r}) = {actual!r}, expected {expected!r}"

print(f"OK - {len(OUTCOME_CASES)} outcome case(s), {len(DURATION_CASES)} duration case(s) passed")
