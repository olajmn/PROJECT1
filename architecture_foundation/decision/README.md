# Decision

**Status: split.** The routing half is **CURRENT** (real, working code in
the prototype, just never named "Decision"). The intervention-policy half
is **EXPLORATORY** (no channel for it exists at all yet).

What happens next, given parsed input and current state. Two genuinely
different jobs share this name:

## 1. Routing (current)

Given a parsed Feedback signal (or a pending clarification, or a duration-
change request), decide which branch to take: replan, advance a step, mark
a goal complete, or check in without changing anything. This already
exists, today, as the branching logic inside `frontend/app.py`'s
`/feedback` route - it has just never been factored out and named as its
own responsibility.

## 2. Intervention policy (exploratory)

Given a discrepancy from `../user_model/`, decide whether it's worth
surfacing to the user unprompted - and if so, whether as a visible signal
(see `../interface/visual_identity/`) or an explicit message. Requires all
of: enough confidence, a discrepancy large enough relative to this user's
own variability, a cooldown since the last time this was raised, and an
actual next step to offer (never surveillance without a point). None of
this exists yet - there is no channel in the prototype for the agent to
say anything unprompted at all (confirmed directly against the code, not
assumed).

## Boundary

Decision does not itself interpret text (that's `goals/feedback/`), does
not itself hold the expectation being checked (that's `../user_model/`),
and does not itself perform the resulting Action/Execution - it only picks
which of those happens next.

## Reference implementation

Routing: `frontend/app.py`'s `/feedback` route (the `if`/`elif` chain over
`outcome_value`). Intervention policy: none - explicitly unbuilt.
