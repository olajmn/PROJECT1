# backend

This is the agent's brain — the code that turns a goal into a plan, and
a plan into "what to do right now."

Named `backend` to match the architecture terminology in
`../docs/03-architecture.md` (backend vs. future frontend).

Run everything from the **project root**, using `-m` (see `../CONVENTIONS.md`
§ Environment for why).

Organized by topic since 2026-08-25, replacing an earlier
`agent/specialized/` vs. `agent/distributed/` reuse-based split:
`foundation/` (what the agent understands, by topic), `goals/` (the
Goal/Plan/Feedback Domain, one subfolder per component), `reasoning/`
(the one boundary every model call passes through), `infrastructure/`
(shared technical machinery), `memory/` and `world/` (Domains, not
built) - see `../docs/03-architecture.md` § System structure for the
full reasoning.

Cleaned up 2026-08-27: `foundation/language/` and
`foundation/meaning(maybe)/` removed (empty, no code, and no
corresponding component anywhere in `architecture_foundation/` to
build toward). `foundation/memory/` relocated to top-level `memory/` -
Memory is its own Domain in `architecture_foundation/`, not a Faculty
nested under Foundation. `backend/reasoning/` established the same
day, once `goals/feedback/` became a second, independent caller of
the model call previously private to `goals/plan/`.

### `foundation/` — what the agent understands

| File | Responsibility | Run with |
|---|---|---|
| `foundation/time/` | Deterministic interpretation of temporal expressions and durations - the temporal understanding Faculty (Time is the corresponding Domain). Split into `time_data/` (recognized phrase tables) and `time_logic/` (`phrase_matching.py`, `duration_resolution.py`, `frozen_duration.py`, `relative_time.py`) | (imported by others, not run directly) |

`time/` is the only established Faculty. No other scaffold is kept
here speculatively - see `architecture_foundation/foundation/README.md`
on why a Faculty has to be earned through demonstrated reuse, not
proposed ahead of any code.

### `goals/` — Domain

| File | Responsibility | Run with |
|---|---|---|
| `goals/goal/resolver.py` | Goal identity/grouping - `get_latest_for_all_goals()`, `get_latest_for_goal()`, `get_history_for_goal()` | (imported by others, not run directly) |
| `goals/feedback/feedback_parser.py` | Deterministic (no LLM) parsing of free-text feedback: outcome parsing (action_completed/action_not_completed/action_in_progress/goal_completed) and duration-change requests, including the recognized phrases themselves (`GOAL_COMPLETED_PHRASES`, etc.) | (imported by others, not run directly) |
| `goals/feedback/acknowledger.py` | Display-only acknowledgment for feedback `parse_outcome()` couldn't classify (`acknowledge()`) - via Reasoning, falls back to a fixed string on any failure | (imported by others, not run directly) |
| `goals/plan/planner.py` | Goal → structured plan, `replan()` (plan + feedback → updated plan), and the Vision/cancellation decisions (`set_goal_vision()`, `archive_vision()`, `cancel_goal()`). Orchestration + Plan shape/prompts | `.venv/bin/python -m backend.goals.plan.planner` |
| `goals/plan/model_client.py` | Plan-specific JSON-shape validation (`ask_model()`) on top of the shared Reasoning call | (imported by others, not run directly) |
| `goals/plan/step_generator.py` | The narrower model call that fills in a plan's step list (`generate_steps()`) | (imported by others, not run directly) |
| `goals/plan/action_reader.py` | Show just the current Action (`now`) from the latest plan | `.venv/bin/python -m backend.goals.plan.action_reader` |

`goals/plan/` holds four files, not a data/logic pair the way
`foundation/time/` does, since planner.py's `PLAN_KEYS` and prompts
stay alongside `generate_plan()`/`replan()` (see that file's docstring
for why) while `model_client.py`/`step_generator.py` are separate,
narrower mechanisms it calls into.

### `reasoning/` — the model-call boundary

| File | Responsibility | Run with |
|---|---|---|
| `reasoning/model_client.py` | The one raw call to the local model (`send_message()`) every other component goes through - no interpretation, no validation, just system+user in, text out | (imported by others, not run directly) |

### Root level

| File | Responsibility | Run with |
|---|---|---|
| `infrastructure/data_persistence.py` | Save/load Goals/plans to/from `../data/plans.json` and Visions to/from `../data/visions.json` - **Infrastructure**, not a Domain or Faculty: reused by everything, understands none of it | (imported by others, not run directly) |
| `memory/` | Empty - see its own `__init__.py` for why it exists at all | — |
| `world/` | Empty - see its own `__init__.py` for why it exists at all | — |

## Where the interface lives

`frontend/` (the local web UI for talking to this agent) is a
top-level sibling of `backend/`, not a subpackage inside it - see
`../frontend/README.md` and `../docs/03-architecture.md`
§ Long-term architecture for why: it's the channel a human reaches the agent
through, not part of the agent's own cognition.

See `../docs/03-architecture.md` for the full architecture and
`../docs/04-current-state.md` for what's built vs. still planned.
