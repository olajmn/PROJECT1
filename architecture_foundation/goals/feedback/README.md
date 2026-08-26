# Feedback

**Status: CURRENT** - proven and working in the prototype.

What actually happened, reported by the user, closing the loop back into
Plan (replanning).

## Owns

Deterministic interpretation of free text into a structured signal - one of
a small, fixed set of outcomes, or an explicit "don't know" rather than a
guess. This is a specific instance of a broader pattern this skeleton
expects to recur (see `../../reasoning/README.md`'s note on
"Interpretation/Parsing" upstream of Memory): recognize what you can name
from an explicit list, admit what you can't, never let an LLM guess a
true/false judgment that changes system state.

## Boundary

Architecturally thinner than Goal/Plan on purpose in the prototype today -
no persistent structure of its own beyond a text field on the next record
and a routing decision. Whether a fuller version needs to be more
explicitly structured is an open question, not decided here - see
`DECISIONS.md`.

## Reference implementation

`backend/goals/goal_logic/feedback_parser.py` - `parse_outcome()`,
`requests_duration_change()`. Deliberately not LLM-based; see that file's
own docstring and the prototype's `docs/05-decisions.md` #1 for why.
