# backend

This is the agent's brain — the code that turns a goal into a plan, and
a plan into "what to do right now."

Named `backend` to match the architecture terminology in
`../docs/08-technical-architecture.md` (backend vs. future frontend).
As of 2026-08-24, "the agent itself" more precisely means `agent/`
inside here - `backend/` is the wider umbrella, also holding `world/`
(external data, not built) and `storage.py`.

Run everything from the **project root**, using `-m` (see `../CONVENTIONS.md`
§ Environment for why).

Split 2026-08-24 into `agent/` (the agent's own cognition -
`specialized/` and `distributed/` inside it) and `world/` (external
data the agent could reach out for - deliberately empty, see its own
`__init__.py`), with `storage.py` staying at this root level - see
`../docs/08-technical-architecture.md` § Faculties for the full
reasoning.

**Vocabulary note (same day):** "Faculty" is this project's word for a
module. `specialized/` holds narrow faculties (one product concept
each); `distributed/` holds broad faculties (reused across more than
one narrow faculty). Two folder names, one concept, described by
breadth rather than by two separate category words - see
`../docs/08-technical-architecture.md` § Faculties, terminology note.

**Resolved, same day:** `storage.py` passes the broad-faculty reuse
test (imported by every narrow faculty, and by `devtools/app.py`
directly) but fails the actual Faculty definition - it understands
nothing about what it saves, just moves bytes. That gap is
**Infrastructure**, a fourth category - see
`../docs/08-technical-architecture.md` § Faculties, "Infrastructure: a
fourth category," for the full reasoning.

### `agent/specialized/` — narrow faculties: one product concept each

| File | Responsibility | Run with |
|---|---|---|
| `agent/specialized/plan.py` | Goal → structured plan, and `replan()` (plan + feedback → updated plan). Both call the LLM | `.venv/bin/python -m backend.agent.specialized.plan` |
| `agent/specialized/goal.py` | Goal identity/grouping - `get_board()`, `get_latest_for_goal()`, `get_history_for_goal()` | (imported by others, not run directly) |
| `agent/specialized/outcome_classifier.py` | Deterministic (no LLM) classification of free-text feedback into done/not_done/in_progress/goal_done - the logic; `outcome_phrases.py` is the data it uses. Currently used only by Goal's own feedback flow - not (yet) reused elsewhere, which is why it lives here and not in `distributed/` despite sharing its phrase-matching technique with `distributed/timeperiod/` | (imported by others, not run directly) |
| `agent/specialized/outcome_phrases.py` | The recognized feedback phrases themselves (`GOAL_DONE_PHRASES`, `RULES`, etc.) - Cognition (the fixed "law"), not Recognition (the "judge" that applies it - see `outcome_classifier.py`) | (imported by others, not run directly) |
| `agent/specialized/today.py` | Show just today's immediate action from the latest plan | `.venv/bin/python -m backend.agent.specialized.today` |

### `agent/distributed/` — broad faculties: reused across more than one narrow faculty

| File | Responsibility | Run with |
|---|---|---|
| `agent/distributed/timeperiod/` | Understanding "when" a plan should span - resolves/describes recognized day segments and week/month/year phrases into a real clock window or calendar date range, honest about what it can't parse. A package (`matchers.py`/`resolve.py`/`frozen.py`) since 2026-08-24, once one file stopped being the natural unit - see its own `__init__.py` | (imported by others, not run directly) |
| `agent/distributed/timesegments.py` | The recognized time phrases/patterns themselves (`DAY_SEGMENTS`, `PERIOD_PHRASES`, etc.) - Cognition (the fixed "law"), not Recognition (the "judge" that applies it - see `timeperiod/matchers.py`) | (imported by others, not run directly) |

### Root level

| File | Responsibility | Run with |
|---|---|---|
| `storage.py` | Save/load plans (and feedback) to/from `../data/plans.json` - **Infrastructure**, not a Room or Faculty: reused by everything, understands none of it | (imported by others, not run directly) |
| `world/` | Empty - see its own `__init__.py` for why it exists at all | — |

## Where the interface lives

`devtools/` (the local web UI for talking to this agent) moved to be a
top-level sibling of `backend/`, not a subpackage inside it, 2026-08-24
- see `../devtools/README.md` and `../docs/08-technical-architecture.md`
§ Faculties for why: it's the channel a human reaches the agent
through, not part of the agent's own cognition.

See `../docs/08-technical-architecture.md` for the full architecture and
`../docs/09-mvp.md` for what's built vs. still planned.
