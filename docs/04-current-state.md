# 04 — Current State

What is true about the project right now. Read this before anything else
in `docs/` — see `COLLABORATION.md` for why, and for how to treat what's
written here (fact vs. hypothesis vs. decision vs. open question).

This file is a snapshot, not a log — it describes the present, not how it
got there. It goes stale the moment something changes; whoever changes it
updates this file before finishing (see `COLLABORATION.md`, "Before
finishing").

## 1. What exists

```text
backend/
  foundation/       Agent capabilities / understanding
    time/           Built - temporal understanding Faculty
  goals/            Domain - goal/ (identity/grouping), feedback/ (parsing),
                    plan/ (goal -> plan, plan + feedback -> replan, action/right_now)
  infrastructure/   Shared technical machinery - data_persistence.py
                    saves/loads JSON (goals/plans and, since 2026-08-26,
                    Vision separately), understands none of what it stores
  memory/           Domain - empty by design, agent's own history not yet
                    organized as its own capability
  world/            Domain - empty by design, no live external data access today
devtools/           Local Flask web UI - the only working interface
data/               Local storage, git-ignored (personal data) - plans.json
                    and, since 2026-08-26, visions.json
docs/               This vault
tools/              Standalone dev utilities, no runtime relationship
                    to the agent (e.g. tools/architecture_mapper,
                    tools/docs_lint.py, tools/docs_check.py)
```

The current backend structure reflects four distinct architectural
concepts (see `03-architecture.md` for the full definitions):

- **Domains** — areas the system operates on
- **Faculties** — reusable capabilities for understanding or interpreting
- **Infrastructure** — shared technical machinery
- **devtools/** — the interface through which a human reaches the agent,
  not part of the agent's own cognition

The only established Faculty today is **temporal understanding**,
implemented under `foundation/time/`. The Time Domain and the temporal
understanding Faculty are related but distinct: Time is what the system
operates on, temporal understanding is the capability the agent uses to
make sense of it.

No other Faculty is established yet under `foundation/` - speculative
empty scaffolds for unproven Faculties (formerly `language/`,
`meaning(maybe)/`) were removed 2026-08-27 rather than kept as
placeholders; a Faculty is added here only once real code earns it
through demonstrated reuse, not proposed ahead of any.

**Vision** (added 2026-08-26) is a fifth concept, deliberately none of
the four above - not a Domain, Faculty, or pipeline stage. It's
optional, cross-goal context (`data/visions.json`, an optional
`vision_id` on a Goal record); see `03-architecture.md` § Vision for
what it is and isn't. The conceptual model is now
**Vision / Goal / Plan / Action / Feedback** - "Action" replaces
"Task"/"today's action" as the term used across docs and the UI
(the `right_now` field name is unchanged, still embedded in persisted
data/the LLM prompts - see `06-development.md`, 2026-08-20, for why.
`today.py`'s script name was left as-is for the same reason at the
time, then renamed to `action_reader.py` on 2026-08-27 once it was
clear that one was just a rename, no persisted-data cost).

**Security status:** whole-disk encryption via macOS FileVault is on
for this machine (covers the "stolen/lost laptop" scenario). No
application-level encryption of `data/plans.json` itself yet - deferred
until this becomes a multi-user or cloud product, see
`05-decisions.md`. No encryption in transit - not relevant while Ollama
is local-only.

## 2. What works

Prototype 0.1's full loop is closed end-to-end:

```text
Goal
 ↓
Plan
 ↓
Action
 ↓
User feedback
 ↓
Replan
 ↓
New action
```

Concretely:

| Capability | File |
|---|---|
| Goal -> plan | `backend/goals/plan/planner.py` (`generate_plan`) |
| Plan saved | `backend/infrastructure/data_persistence.py` |
| Action (right now) | `backend/goals/plan/action_reader.py` reads `plan.right_now` |
| User reports progress | `devtools/app.py` (`/feedback`) |
| Plan adjusts | `backend/goals/plan/planner.py` (`replan`) |
| Temporal understanding | `backend/foundation/time/` |
| Vision created / linked to a Goal | `devtools/app.py` (`/vision`, `/goal`) |
| Local web UI | `devtools/app.py` - vision form, goal form, feedback, per-step done/no, history, completed |

"Works" means the mechanism runs correctly - the code calls the LLM,
saves, and displays a result. It does not mean the LLM's answers are
always accurate; it has already been caught hallucinating a specific,
unfounded detail (see `06-development.md`).

## 3. What's half-built

- `planning/` has not yet been split into a data/logic structure the
  way `foundation/time/` and `goals/` have.
- **Vision** - create and link-to-a-goal are built; editing/deleting an
  existing Vision is not. A Goal's Vision is never actually supplied to
  the LLM yet (`generate_plan()`/`replan()` both ignore `vision_id`) -
  deliberate for now, see `03-architecture.md` § Vision.

## 4. What's not built

- **Memory** - the agent doesn't yet use its own history; `memory/`
  is an empty placeholder (a Domain, not nested under `foundation/`).
- **Hierarchical step list** - a goal's plan is currently one flat step
  list, not nested phases with their own sub-steps.
- **Knowledge / RAG** - sketched, not implemented.
- **Acting** - the agent reasons about what should happen; it doesn't yet
  perform external actions such as creating files or calling APIs.
- **Live external data** - `world/` is a deliberate empty placeholder.
- **Goal auto-completion** - finishing every step does not automatically
  mark a goal complete; the user still confirms explicitly. Deliberate,
  not an oversight.

## 5. Current structure

The current implementation can be summarized as:

```text
Domains
  Time, Goals, Planning, Tasks, Conversation, History, Knowledge, World
  (not all implemented independently)

Faculties
  Temporal understanding

Infrastructure
  Persistence

Interface
  devtools/
```

Not all of these are currently implemented as independent components -
this describes the architectural concepts currently recognized by the
project; § What exists, § What works, and § What's not built above are
the authoritative source for what's actually built.

Vision is not in the Domains list above, deliberately - see
`03-architecture.md` § Vision for why (not a Domain, Faculty, or
pipeline stage; a small capability inside Goals/Planning).

Time is currently the only Domain that has produced an established
Faculty: temporal understanding. Other Domains may or may not
eventually produce corresponding Faculties. Temporal understanding
handles temporal expressions and durations deterministically, without
requiring the LLM to interpret them.

`data_persistence.py` is Infrastructure because it stores and retrieves
data without understanding what that data represents.

`devtools/` sits outside `backend/` entirely - it's the channel through
which a human reaches the agent, not part of the agent's own cognition.

Full architectural definitions and relationships: `03-architecture.md`.

## 6. Current decisions

Stable, not casually revisited (see `COLLABORATION.md` rule 4):

- LLM backend: Ollama (local, `llama3.1:8b`), not a paid API - no cost, no
  internet dependency.
- Storage: local plaintext JSON, append history, never overwrite. Not
  moving to SQL.
- Feedback outcome (action_completed/action_not_completed/action_in_progress/
  goal_completed) is parsed deterministically, never left to the LLM to judge.
- Testing on real use takes priority over adding more features.
- Vision is optional, lightweight context (an id+text store, an optional
  foreign-key-style reference on a Goal) - not a relational hierarchy, not
  duplicated free text per goal.

Full list with reasoning: `05-decisions.md`.

## 7. Open questions

- Flat vs. hierarchical step list - not designed, needs its own pass.
- Should a goal auto-complete when every step is done? Real tension
  between one-shot goals and ongoing habit goals, not resolved.
- Future Faculties should emerge from demonstrated reuse, not be
  predetermined now - none beyond temporal understanding are settled.
- Visual design - wants a holistic pass, not one color fixed at a time.
- Whether/how a Goal's Vision ever gets summarized into the LLM's
  context when planning/replanning - deliberately not decided or built
  yet, see `03-architecture.md` § Vision.
- Whether editing/deleting an existing Vision is worth building, once
  there's real usage to learn from.

## 8. Next step

1. Pick one of Memory / hierarchical steps / Knowledge-RAG / Acting to
   actually build - not more than one at a time.

(The Action/Task/`right_now`/"today's task" terminology drift an
earlier architectural pass flagged as worth resolving before picking
one of these is now done, alongside implementing Vision - see
`06-development.md`, 2026-08-26.)
