# 03 — Architecture

> How the agent is structured: what it's made of, how the pieces relate, and what principles guide how it grows. The map, not a master note — not the story of how this structure was reached (see [[06-development]]), not the reasoning behind a specific choice (see [[05-decisions]]), and not what's actually implemented right now (see [[04-current-state]]).

## 1. Architectural overview

### Diagram

See `03-architecture.drawio` in this folder — a visual map of the agent's architecture and its planned extensions. Green indicates built components; gray dashed elements are planned.

### Program

> The agent helps a person turn a goal into a concrete plan.

The architecture is organized around the progression from **goal → plan → action → feedback → replan**.

### Three architectural lenses

| Dimension     | Question                        | Examples                                      |
| ------------- | ------------------------------- | ---------------------------------------------- |
| **Domains**   | What does the system operate on? | Time, Goals, Planning, Conversation, Knowledge |
| **Faculties** | What can the agent understand or interpret? | Temporal understanding, Language, Semantics |
| **Pipeline**  | What happens, in what order?    | User → Reasoning → Planning → Action → Result |
| **Infrastructure** | What technical machinery supports the system? | Persistence, storage, external services |

These are complementary views of the same system rather than competing structures.

---

## 2. System structure

### Domains

A **Domain** is an area of responsibility or subject matter that the system operates on.

| Domain       | Responsibility                            |
| ------------ | ------------------------------------------ |
| Time         | Durations, timeframes, dates, deadlines   |
| Goals        | Define and manage user goals              |
| Planning     | Turn goals into plans and revise them     |
| Tasks        | Represent concrete actions                |
| Conversation | Interaction between user and agent        |
| History      | Preserve and retrieve past activity       |
| Knowledge    | Retrieve relevant user-provided knowledge |

`right_now` is currently represented inside the plan structure, but architecturally it should eventually represent an action or trigger rather than another time horizon.

### Faculties

A **Faculty** is a reusable area of agent understanding that is not tied to one Domain or one pipeline stage.

A Domain does not automatically get its own Faculty just because the agent needs to reason about it. Time, for example, is a Domain (what the system operates on); temporal understanding is the corresponding Faculty (the agent's reusable capability to interpret it - recognizing what "this weekend" means, comparing durations, etc.). Temporal understanding is the first established Faculty. Other candidates include Language and Semantics, but a Faculty should emerge through actual reuse across the system rather than being created purely as a conceptual category.

### Infrastructure

**Infrastructure** is shared technical machinery used by the system but which does not itself represent something the agent understands.

Persistence is the current example.

Infrastructure therefore differs from a Faculty:

> A Faculty understands something. Infrastructure moves, stores, or provides something.

### Pipeline

The Pipeline describes execution order:

```text
User → Reasoning → Planning → Action → Result
```

It is orthogonal to both Domains and Faculties.

A Domain describes **what the system operates on**.
A Faculty describes **what the agent understands**.
The Pipeline describes **what happens, and in what order**.

The Action stage is reasoning-only today - the agent doesn't yet perform external actions (creating a file, calling an API). Building that out is a parked idea: see [[06-development]] § Parking Lot.

---

## 3. Runtime architecture

```text
UI
 ↓
Backend
 ↓
Reasoning
 ↓
Planning / Action
 ↓
Persistence / External systems
 ↓
UI
```

The UI and backend are separate architectural layers. The current interface may change without requiring the agent's core logic to become tied to a particular frontend.

The backend is therefore treated as the durable core, while interfaces are replaceable clients.

---

## 4. Architectural principles

### 1. Local-first

The user's device remains the authoritative copy of their data.

### 2. Portable

User data should remain in open, human-readable formats where practical.

### 3. Replaceable infrastructure

Cloud services, synchronization servers and external APIs are dependencies, not the source of truth.

### 4. Privacy by architecture

Sensitive personal data should remain local where possible. If synchronization is introduced, it should preserve end-to-end encryption and user ownership.

### 5. Start simple

Do not introduce databases, vector stores, services or distributed infrastructure until the current implementation creates a real, felt need for them.

> The app should be able to disappear without the user's history disappearing.

See [[05-decisions]] for the reasoning behind specific architectural decisions.

---

## 5. Architectural components

### Time — Domain / Temporal understanding — Faculty

Time is a Domain (durations, timeframes, dates, deadlines); temporal understanding is the Faculty that provides deterministic interpretation of temporal expressions and durations.

It handles concepts such as:

* temporal expression matching
* duration resolution
* fixed goal timeframes
* relative duration comparison

Time interpretation is deliberately separated from LLM reasoning: **code decides, the model is told**.

Activity-specific interpretation of duration remains outside the established temporal-understanding Faculty for now.

### Planning — Domain

Planning turns a goal into a concrete sequence of time horizons and actions, and supports revision through feedback:

```text
Goal
 ↓
Plan
 ↓
Action
 ↓
Feedback
 ↓
Replan
```

### Knowledge — Domain

Knowledge allows the agent to reason using material supplied by the user rather than relying exclusively on model knowledge or live external information.

The planned architecture is retrieval-based:

```text
User documents
      ↓
Retrieval
      ↓
Relevant context
      ↓
Reasoning
```

The implementation should remain local and simple until scale creates a real need for dedicated retrieval infrastructure.

A fact-checking capability built on top of this Domain - verifying a claim against retrieved sources rather than answering from training alone - is a parked idea, not yet designed: see [[06-development]] § Parking Lot.

### Memory — Domain

Memory is the agent's accumulated record of the user's goals, plans, activity and history.

It should remain local, portable and independently accessible from the application itself.

The exact long-term retrieval and organization model is intentionally not fixed yet. Whether a corresponding Faculty (e.g. how the agent selects, interprets, and relates past experience) eventually emerges is deliberately left open, not decided now.

### World — Domain

World represents live external information and services the agent may eventually use when reasoning or acting — for example weather, calendars, maps and other external sources.

World is distinct from Knowledge:

* **Knowledge** = material the user has supplied
* **World** = live information from external systems

---

## 6. Long-term architecture

> Vision, not current implementation.

The long-term system can be understood as a loop between the user, the world, the agent's memory and its reasoning:

```text
                     PERSONAL AGENT

                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
       MEMORY            WORLD             USER
          │                │                │
          │          information          goals
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                       REASONING
                           ↓
                  ┌────────┴────────┐
                  ↓                 ↓
               PLANNING           ACTION
                  ↓                 ↓
               schedule       interaction
                  │                 │
                  └────────┬────────┘
                           ↓
                        RESULT
                           ↓
                         MEMORY
                           ↺
```

Future interfaces — web, iOS or Android — should sit above the same backend and portable data rather than defining the underlying architecture.

Future synchronization should preserve the local-first principle: the user's devices remain authoritative, while synchronization infrastructure acts as a replaceable mechanism rather than the owner of the data.

None of this is being built as part of the current MVP. See [[02-product]] and [[06-development]].

---

## See also

* [[02-product]]
* [[04-current-state]]
* [[05-decisions]]
* [[06-development]]
