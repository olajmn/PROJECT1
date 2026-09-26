# Memory

**Status: NEXT** - a real, identified gap, not hypothetical. The data
already exists; the capability to use it doesn't.

The agent's own raw operational history - what actually happened, across
every Goal, Plan, Action, and Feedback. The source of truth for anything
derived (see `../user_model/`).

## Owns

Read access to the agent's own history as a first-class capability, not an
implicit side effect of Goal identity.

## Boundary

- Not Knowledge (`../knowledge/`) - Memory is the agent's own recorded
  experience; Knowledge is material the user has separately supplied.
- Not the same as "state" - the current state of an in-progress Goal is
  just the latest view into Memory, not a second thing to keep in sync
  with it (see `ARCHITECTURE.md`).
- Any derived summary (see `../user_model/`) must remain reconstructable
  from Memory - Memory is never allowed to become a thing only the derived
  layer can explain.

## Where a retrieval mechanism would go, if ever needed

Not a subfolder here on purpose (an empty `retrieval/` folder would be
structure without a use yet). Start with deterministic filtering (by goal,
date range, keyword) if and when cross-goal lookups are actually needed;
only reach for embeddings/vector search if filtering demonstrably isn't
enough. See `ARCHITECTURE.md`'s RAG/embeddings section.

## Reference implementation

The raw data already exists and is technically complete:
`backend/storage/project_persistence.py`'s `load_history()`/
`load_project_history()`. What's missing is organizing this as its own
capability rather than reading it ad hoc from within project panes.
