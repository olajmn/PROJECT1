# Execution

**Status: FUTURE** - named and explicitly parked in the prototype's own
docs, not designed.

The agent actually performing something in the real world - creating a
file, calling an API, using a tool - rather than only reasoning about what
should happen.

## Not to be confused with Action

Execution is the agent's own capability to act. `goals/action/` is the
user's own immediate next step. These are different responsibilities with
different owners (agent vs. user) that happen to both be describable as
"doing something" - kept as two separate, differently-named components on
purpose. See `ARCHITECTURE.md`.

## Boundary

Downstream of `../decision/` - Execution does what Decision decided should
happen, it doesn't decide anything itself.

## Likely direction, not a decision

Raised, not decided: Execution is a plausible candidate for delegating to
an existing external execution/tool-use runtime rather than building
tool-calling/computer-use from scratch - the agent's differentiated value
is the Vision/Goal/Plan/Feedback loop and (if built) User Representation,
not reimplementing generic execution infrastructure. This is a direction
worth evaluating when Execution actually gets picked up, not a commitment
made here.

## Reference implementation

None. The prototype's own `docs/04-current-state.md` names this directly:
"the agent reasons about what should happen; it doesn't yet perform
external actions."
