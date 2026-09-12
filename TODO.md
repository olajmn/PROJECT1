# TODO

Not a duplicate of `docs/04-current-state.md` - that file is the full,
factual account of what's true now, including known bugs/gaps and the
reasoning behind each. This file only tracks which of those are
actually being worked on (**Active**), plus a flat, numbered catalog
of everything identified so far (**Queue**), so the total scope is
visible at a glance without implying priority or sequence.

An item moves from Queue to Active only when deliberately chosen as
next; it stays in Queue, undecided, until then - a known gap does not
need to be urgent to be worth recording (see `docs/04-current-state.md`
for that same principle applied to documentation, not just this file).

## Active

Nothing yet - items land here only once chosen out of the Queue below.

## Queue

Every known gap, bug, or unbuilt piece identified so far, numbered for
a quick count - not prioritized, not sequenced. Each points back to
where the actual reasoning lives (`docs/04-current-state.md` unless
noted) rather than repeating it here; update that file first when
something changes, then this list if the item's status changes too.

1. **Topic continuity / multi-goal free conversation** - `cli.py`'s `ChatFocus` holds one goal only, and nothing detects a mid-conversation topic switch. § 5, § 9, § 10.
2. **Vision choice at goal-creation time** - Set Goal and free conversation always create a goal unlinked; linking only happens afterward via Active. § 5, § 10.
3. **Structured step-completion signal** - `advance_step()` exists in `planner.py` but has no route or UI control. § 5, § 9, § 10.
4. **Accepting a `suggested_action` never produces a step tree** - the acceptance branch sets `now` directly, never calls `generate_structure()`. § 5.
5. **`clarification`+`now` leak** - the `clarification` branch doesn't null `now` the way the `suggested_action` branch does. § 5.
6. **Session end detection** - no graceful-shutdown hook sets a Session's real `ended_at`. § 5, § 10.
7. **Vision-archive timing in the Session log** - `archive_vision()` doesn't stamp when archiving happened, only creation. § 5, § 10.
8. **Module Library unwired** - five working Modules, reachable from nothing. § 5.
9. **Node 3's second capability** - `select_capability()` can only ever return `"planning"` or `None`. § 7, § 10.
10. **Memory domain** - not built at all. § 7, § 9.
11. **Knowledge / RAG** - not built at all. § 7.
12. **Decomposition / zoom** - no way to increase an already-generated step's resolution on demand. § 7.
13. **Acting** - the agent performs no external action. § 7.
14. **Continuity / proactivity** - no scheduler or background behavior. § 7.
15. **Node 1 re-voicing** - whether Node 1 should re-voice a capability's output verbatim or in its own words is undecided. § 9; see also `docs/03-architecture.md` Part 3 § 8.
