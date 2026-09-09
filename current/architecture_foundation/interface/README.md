# Interface

**Status: CURRENT** - a working instance exists; not yet designed as a
product frontend.

The presentation layer a person actually interacts with - not part of the
agent's own cognition, and deliberately replaceable without the agent's
core logic changing.

## Owns

Rendering state and collecting input. Nothing in this component should
make a decision the way `../decision/` does, or interpret meaning the way
`goals/feedback/` does - if it does, that logic has drifted out of its
proper component and into the interface layer, which is a maintenance
smell worth catching, not a pattern to repeat here.

## Boundary

Swappable by design - a future web app, mobile app, or voice interface
should be able to sit on the same backend and portable data without the
agent's reasoning needing to change. See the prototype's own
`docs/03-architecture.md` § Long-term architecture on interfaces as
replaceable clients.

## `visual_identity/`

One possible future expression of this layer - see that folder's own
README. Not a separate component; folded in here deliberately.

## Reference implementation

`frontend/` in the prototype - a local Flask/Jinja devtool, explicitly not
the product's eventual real frontend (see that directory's own README in
the prototype).
