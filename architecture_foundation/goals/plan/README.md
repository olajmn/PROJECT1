# Plan

**Status: CURRENT** - proven and working in the prototype, with one known
data-model issue flagged below.

How one specific Goal should be pursued, across time horizons (from broad -
a year out - down to the narrowest, which is Action).

## Owns

Strategy content for one Goal: what should happen at each time horizon it
actually spans, and how that content is revised when Feedback comes in
(replanning).

## Boundary - the one thing worth flagging explicitly

In the prototype's actual code, Plan and Action are **the same data
structure and the same model call** - the narrowest horizon (`right_now`)
is a field inside Plan's own dict, produced by the same LLM response as
every broader horizon. This skeleton models Plan and Action as two
components anyway (see `../action/README.md`), because the prototype's own
interface already treats them as conceptually separate (rendered as two
different labeled sections), and because that separation is what makes
Action able to stand on its own if Execution is ever built. This is flagged
as something to actually resolve during the later keep/move/rewrite/discard
pass, not a decision made here.

## Reference implementation

`backend/planning/planner.py` - `generate_plan()`, `replan()`. See its
docstrings for exactly where a future Vision summary (see `../../vision/`)
could be added to the model's context - noted, not wired in yet.
