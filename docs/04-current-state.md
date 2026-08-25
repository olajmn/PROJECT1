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
    language/       Empty scaffold, no established Faculty
    memory/         Empty scaffold, no established Faculty
    meaning(maybe)/  Empty scaffold, unresolved
  goals/            Domain - goal identity/grouping, feedback classification
  planning/         Domain - goal -> plan, plan + feedback -> replan, today's action
  infrastructure/   Shared technical machinery - data_persistence.py
                    saves/loads JSON, understands none of what it stores
  world/            Domain - empty by design, no live external data access today
devtools/           Local Flask web UI - the only working interface
data/               Local storage, git-ignored (personal data)
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

Other potential Faculties are not yet established. Empty scaffolds such
as `language/`, `memory/`, and `meaning(maybe)/` do not by themselves
constitute Faculties.

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
Today's action
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
| Goal -> plan | `backend/planning/plan.py` (`generate_plan`) |
| Plan saved | `backend/infrastructure/data_persistence.py` |
| Today's action | `backend/planning/today.py` |
| User reports progress | `devtools/app.py` (`/feedback`) |
| Plan adjusts | `backend/planning/plan.py` (`replan`) |
| Temporal understanding | `backend/foundation/time/` |
| Local web UI | `devtools/app.py` - goal form, feedback, per-step done/no, history, completed |

"Works" means the mechanism runs correctly - the code calls the LLM,
saves, and displays a result. It does not mean the LLM's answers are
always accurate; it has already been caught hallucinating a specific,
unfounded detail (see `06-development.md`).

## 3. What's half-built

- `planning/` has not yet been split into a data/logic structure the
  way `foundation/time/` and `goals/` have.

## 4. What's not built

- **Memory** - the agent doesn't yet use its own history; `foundation/memory/`
  is an empty scaffold.
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
- Feedback outcome (done/not-done/in-progress) is classified
  deterministically, never left to the LLM to judge.
- Testing on real use takes priority over adding more features.

Full list with reasoning: `05-decisions.md`.

## 7. Open questions

- Flat vs. hierarchical step list - not designed, needs its own pass.
- Should a goal auto-complete when every step is done? Real tension
  between one-shot goals and ongoing habit goals, not resolved.
- Future Faculties should emerge from demonstrated reuse, not be
  predetermined now - none beyond temporal understanding are settled.
- Visual design - wants a holistic pass, not one color fixed at a time.

## 8. Next step

1. Pick one of Memory / hierarchical steps / Knowledge-RAG / Acting to
   actually build - not more than one at a time.
