# User Representation

**Status: EXPLORATORY** - a hypothesis under real consideration, not a
committed feature. May never be built if it doesn't earn its complexity.

A persistent, updated belief about this specific user's patterns, derived
from `../memory/` - what has been generalized from what happened, as
distinct from the raw record of what happened. Produces an expectation
that new observations can be compared against.

## Owns

Expectation and discrepancy, together, as one function - not two:

```text
experience → raw memory → adaptive representation → expectation
    → new observation → discrepancy → updated representation
```

This is why Expectation/Discrepancy is not its own component (see
`COMPONENT_MAP.md`, "Explicitly not components") - it's the predict/
observe/compare/update cycle this component performs, not a second
responsibility next to it.

## Boundary

- Reads only from Memory, never from Knowledge.
- Must remain a rebuildable derived state, never the only record of
  anything - Memory stays the source of truth.
- Does not decide whether to act on a discrepancy - that's `../decision/`.
  This component's job stops at "here's an expectation, and here's how far
  the latest observation is from it."
- Does not claim, and is not evidence of, anything resembling subjective
  experience or consciousness - persistent state, expectation, and
  discrepancy-detection are information-processing properties, not claims
  about the system's inner life. See `DECISIONS.md`.

## Mechanism - deliberately not decided

Not a neural network, not by default. Given a single-user, low-volume,
non-stationary data source, a simple statistical estimator (an exponential
moving average, or a Bayesian update) is the more likely correct starting
mechanism - cheaper, fully inspectable, and workable with very little data.
A neural network becomes worth reconsidering only once there's real
history and enough distinct tracked patterns that shared representation
learning would outperform hand-built estimators - not before. See
`ARCHITECTURE.md` and `COMPONENT_MAP.md`'s "Where mechanisms plug in."

## Reference implementation

None. Nothing in the prototype reads Memory back into reasoning across more
than one Goal's own thread (`replan()` reads one goal's full history, never
another goal's). This is a genuine, not partial, gap.
