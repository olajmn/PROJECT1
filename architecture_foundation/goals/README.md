# Goals

**Status: CURRENT** - the operational loop, proven and working end to end
in the prototype.

The four responsibilities that make up the Goal → Plan → Action → Feedback
loop each have their own folder here (`goal/`, `plan/`, `action/`,
`feedback/`), kept as distinct components even though the prototype's own
data model currently merges two of them (Plan and Action - see
`plan/README.md`). Grouped under one parent folder because they're tightly
sequential and only make sense together; not merged into one component
because the architectural clarification pass that led to this skeleton
found real value in keeping them conceptually separate - see the
prototype's own `docs/06-development.md` for that analysis.

`vision/`, one level up, sits above this whole loop rather than inside it -
see `../vision/README.md` and `ARCHITECTURE.md`.
