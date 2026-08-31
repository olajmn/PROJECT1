# Foundation

**Status: CURRENT** - the analytical lens itself is established and
proven; one Faculty is actually built.

Not a component that does something on its own - this is the Domain /
Faculty / Infrastructure / Pipeline principle the whole rest of this
skeleton is organized by:

- A **Domain** is an area the system operates on (e.g. Time, Goals).
- A **Faculty** is a reusable capability for *understanding or interpreting*
  something, earned through demonstrated reuse across more than one Domain
  - never created just because a concept has a plausible name.
- **Infrastructure** moves, stores, or provides something, without itself
  understanding what it represents (see `../infrastructure/`).
- The **Pipeline** is execution order - orthogonal to the other two.

## The one proven Faculty

Temporal understanding - deterministic interpretation of durations,
timeframes, and deadlines, kept explicitly separate from LLM reasoning
("code decides, the model is told"). No other Faculty is settled yet; empty
scaffolds elsewhere in the prototype (`language/`, a `meaning` placeholder)
do not by themselves constitute one - a Faculty has to actually be reused,
not just proposed.

Whether this Faculty's scope extends beyond parsing (interpreting what a
duration *means*) into behavioral cadence (how often the agent itself
should act, not just how a span of time is understood) is raised but not
designed - see `../DECISIONS.md`'s Exploratory list.

## Boundary

Nothing here is itself an operational component the way `goals/` or
`memory/` are - this folder documents the *rule* by which every other
component in this skeleton was categorized, so that rule has one place to
live rather than being re-explained per component.

## Reference implementation

`backend/foundation/time/` in the prototype - fully working, the reference
for what a real Faculty looks like if another one is ever earned.
