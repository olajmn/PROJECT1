# backend

This is the agent's brain — the code that turns a goal into a plan, and
a plan into "what to do right now."

Named `backend` to match the architecture terminology in
`../docs/03-architecture.md` (backend vs. future frontend).

Run everything from the **project root**, using `-m` (see `../CONVENTIONS.md`
§ Environment for why).

Organized by topic since 2026-08-25, replacing an earlier
`agent/specialized/` vs. `agent/distributed/` reuse-based split:
`foundation/` (what the agent understands, by topic), `goals/` and
`planning/` (Domains, direct siblings rather than nested under an
`agent/` wrapper - `agent/` is gone entirely), `infrastructure/`
(shared technical machinery), and `world/` (external data, not built) -
see `../docs/03-architecture.md` § System structure for the full
reasoning.

### `foundation/` — what the agent understands

| File | Responsibility | Run with |
|---|---|---|
| `foundation/time/` | Deterministic interpretation of temporal expressions and durations - the temporal understanding Faculty (Time is the corresponding Domain). Split into `time_data/` (recognized phrase tables) and `time_logic/` (`phrase_matching.py`, `duration_resolution.py`, `frozen_duration.py`, `relative_time.py`) | (imported by others, not run directly) |
| `foundation/language/` | Empty scaffold, no code yet | — |
| `foundation/memory/` | Empty scaffold, no code yet | — |
| `foundation/meaning(maybe)/` | Empty scaffold, name itself marks it as unresolved | — |

### `goals/` — Domain

| File | Responsibility | Run with |
|---|---|---|
| `goals/goal_logic/goal.py` | Goal identity/grouping - `get_board()`, `get_latest_for_goal()`, `get_history_for_goal()` | (imported by others, not run directly) |
| `goals/goal_logic/outcome_classifier.py` | Deterministic (no LLM) classification of free-text feedback into done/not_done/in_progress/goal_done - the logic; `goal_data/outcome_phrases.py` is the data it uses | (imported by others, not run directly) |
| `goals/goal_data/outcome_phrases.py` | The recognized feedback phrases themselves (`GOAL_DONE_PHRASES`, `RULES`, etc.) | (imported by others, not run directly) |

### `planning/` — Domain

| File | Responsibility | Run with |
|---|---|---|
| `planning/plan.py` | Goal → structured plan, and `replan()` (plan + feedback → updated plan). Both call the LLM | `.venv/bin/python -m backend.planning.plan` |
| `planning/today.py` | Show just today's immediate action from the latest plan | `.venv/bin/python -m backend.planning.today` |

Not yet split into a data/logic pair the way `foundation/time/` and
`goals/` have.

### Root level

| File | Responsibility | Run with |
|---|---|---|
| `infrastructure/data_persistence.py` | Save/load plans (and feedback) to/from `../data/plans.json` - **Infrastructure**, not a Domain or Faculty: reused by everything, understands none of it | (imported by others, not run directly) |
| `world/` | Empty - see its own `__init__.py` for why it exists at all | — |

## Where the interface lives

`devtools/` (the local web UI for talking to this agent) is a
top-level sibling of `backend/`, not a subpackage inside it - see
`../devtools/README.md` and `../docs/03-architecture.md`
§ System structure for why: it's the channel a human reaches the agent
through, not part of the agent's own cognition.

See `../docs/03-architecture.md` for the full architecture and
`../docs/04-current-state.md` for what's built vs. still planned.
