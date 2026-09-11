# Visual Identity

**Status: EXPLORATORY** - a design idea, deliberately not built. No code,
no assets - documentation only, on purpose.

The hypothesis: a very simple, stable visual identity for the agent (an
abstract shape, not necessarily a face) that the user encounters
consistently across sessions - `idle`, `processing`, `speaking`, and
potentially `noticing` as states.

## The one hard rule

Any state shown must reflect a real internal event, never simulated
affect. A `noticing` state, specifically, may only ever be tied to an
actual discrepancy signal from `../../user_model/` and `../../decision/` -
never a random or decorative animation. The same confidence/threshold/
cooldown discipline `../../decision/README.md` describes for an
intervention applies equally to a visual signal - a "notice" state fired on
low-confidence data is exactly as costly to trust as a wrong message would
be.

## Open design question, not resolved here

Whether a face-like shape is actually appropriate at all - it recruits
face-perception (and the expectations that come with it: gaze, attention,
judgment) more strongly than a fully abstract shape (a light, a ring, a
waveform) would. Left open.

## Relationship to the "relational continuity" hypothesis

This component is one *possible* expression of a broader, non-technical
hypothesis: that continuity, specificity, and consistent identity - not
simulated personality or emotion - might be what lets an agent feel like
"mine" over time to the person using it. That hypothesis is a product/
design question, not a claim about the system having feelings or
consciousness, and it doesn't require this component (or `../../user_model/`)
to exist in any particular form to be true or false. See `DECISIONS.md`.

## Reference implementation

None. Fully unbuilt.
