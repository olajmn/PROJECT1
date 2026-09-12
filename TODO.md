# TODO

Not a duplicate of `docs/04-current-state.md` - that file is the full,
factual account of what's true now, including known bugs/gaps and the
reasoning behind each. This file only tracks which of those are
actually being worked on (**Active**), plus a numbered catalog of
everything identified so far, tiered by rough impact (**Queue**), so
both the total scope and a sense of what matters most are visible at
a glance.

An item moves from Queue to Active only when deliberately chosen as
next; it stays in Queue, undecided, until then - a known gap does not
need to be urgent to be worth recording (see `docs/04-current-state.md`
for that same principle applied to documentation, not just this file).

## Active

Nothing yet - items land here only once chosen out of the Queue below.

## Queue

Every known gap, bug, or unbuilt piece identified so far, numbered for
a quick count. Each points back to where the actual reasoning lives
(`docs/04-current-state.md` unless noted) rather than repeating it
here; update that file first when something changes, then this list
if the item's status changes too.

Each item carries two tags: what kind of thing it is, and roughly how
much it matters for moving the actual, working product forward right
now (not effort, not urgency in the "on fire" sense - impact):

- **Bug** - something behaves wrong today, against its own intent. **Step** - nothing is broken; the thing just doesn't exist yet. **Question** - not code at all; a design decision nothing has been built toward either way.
- **Tier 1** - small, contained, causing actually-wrong behavior today. **Tier 2** - contained, low-risk, finishes something already mostly built. **Tier 3** - already-built code, just not wired in. **Tier 4** - a new, large domain - its own multi-day round, not a quick next step. **Untiered** - a pure decision; no code is waiting on it either way, so it isn't "next" in the same sense as the others.

Ordered by tier, not by the number itself - the number is this item's
stable identity (for referring back to it), not its rank.

### Tier 1

1. **`clarification`+`now` leak** (Bug) - the `clarification` branch doesn't null `now` the way the `suggested_action` branch does. § 5.
2. **Accepting a `suggested_action` never produces a step tree** (Bug) - the acceptance branch sets `now` directly, never calls `generate_structure()`. § 5.
3. **Topic continuity / multi-goal free conversation** (Bug) - `cli.py`'s `ChatFocus` holds one goal only, and nothing detects a mid-conversation topic switch. Largest of the three Tier 1 items - discussed as roughly comparable in size to a full session's own work, not a quick fix. § 5, § 9, § 10.

### Tier 2

4. **Vision choice at goal-creation time** (Step) - Set Goal and free conversation always create a goal unlinked; linking only happens afterward via Active. § 5, § 10.
5. **Structured step-completion signal** (Step) - `advance_step()` exists in `planner.py` but has no route or UI control. § 5, § 9, § 10.
6. **Vision-archive timing in the Session log** (Step) - `archive_vision()` doesn't stamp when archiving happened, only creation. § 5, § 10.
7. **Session end detection** (Step) - no graceful-shutdown hook sets a Session's real `ended_at`. Lower actual impact than the others in this tier - the read-side window-bounding fix already makes the derived log accurate without it. § 5, § 10.

### Tier 3

8. **Module Library unwired** (Step) - five working Modules, reachable from nothing. § 5.

### Tier 4

9. **Node 3's second capability** (Step) - `select_capability()` can only ever return `"planning"` or `None`. § 7, § 10.
10. **Memory domain** (Step) - not built at all. § 7, § 9.
11. **Knowledge / RAG** (Step) - not built at all. § 7.
12. **Decomposition / zoom** (Step) - no way to increase an already-generated step's resolution on demand. § 7.
13. **Acting** (Step) - the agent performs no external action. § 7.
14. **Continuity / proactivity** (Step) - no scheduler or background behavior. § 7.

### Untiered

15. **Node 1 re-voicing** (Question) - whether Node 1 should re-voice a capability's output verbatim or in its own words is undecided. § 9; see also `docs/03-architecture.md` Part 3 § 8.
