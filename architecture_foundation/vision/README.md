# Vision

**Status: CURRENT** - proven and working in the prototype.

Optional, lightweight context representing the user's broader direction -
the "why" that can sit above and inform multiple, independent Goals. Not a
renamed long-term Plan (a single Goal's own broad-horizon content is
already correctly part of `goals/plan/`, not this) and not a step in the
operational loop - it sits above `goals/`, not inside it.

## Owns

An id and a text - nothing else. No history, no revisions (a Vision's text
is edited in place if it's ever wrong, not versioned). No relationship
beyond `goals/goal/` optionally carrying a reference to one.

## Boundary

- Does not generate Goals. The relationship is "Vision contextualizes
  Goals," never "Vision generates Goals" - see `ARCHITECTURE.md`.
- Does not currently reach `reasoning/` at all - a Goal's Vision is not yet
  supplied to any LLM call. That's a known, deliberate gap, not an oversight
  - see `DECISIONS.md`.
- Most Goals will have no Vision. That's the normal case, not a partial
  state to fix.

## Reference implementation

Fully built in the prototype: `backend/infrastructure/data_persistence.py`
(`save_vision`/`load_visions`/`get_vision`, a separate `data/visions.json`),
an optional `vision_id` on a Goal record, a creation form and grouped
display in `devtools/`. See the prototype's `docs/03-architecture.md` §
Vision and `docs/05-decisions.md` #17 for the full reasoning behind this
shape - not repeated here.
