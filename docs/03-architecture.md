# 03 — Architecture

> How the agent is structured: what it's made of, how the pieces relate, and what principles guide how it grows. The map, not a master note — not the story of how this structure was reached (see [[06-development]]), not the reasoning behind a specific choice (see [[05-decisions]]), and not what's actually implemented right now (see [[04-current-state]]).

## 1. Architectural Overview

### Diagram

See [[04-current-state]] § Visual Overview for a diagram of the agent's actual current structure. This document (VISION + NOW) has no single visual counterpart of its own — the long-term architecture described in § 6 below is not yet built, so there is nothing yet to diagram beyond what `04-current-state.md` already shows.

### Program

> The agent helps a person turn a goal into a concrete plan.

The architecture is organized around the progression from **goal → plan → action → feedback → replan**.

The conceptual model behind that progression, clarified 2026-08-26 (see [[06-development]]):

- **Vision** — why / the user's overall direction, optionally spanning multiple Goals. Not a pipeline stage.
- **Goal** — what the user wants to achieve. A stable identity.
- **Plan** — how one Goal should be pursued, across time horizons.
- **Action** — what the user does right now. The narrowest, most immediate horizon of Plan.
- **Feedback** — what actually happened, reported back by the user.

Vision sits above this loop, providing optional context; it does not sit inside it. See § Vision for what "above" means concretely; see [[06-development]] for why Action/Task/`right_now`/"today's task" are the same concept under different names.

### Three architectural lenses

| Dimension | Question | Examples |
|---|---|---|
| **Domains** | What does the system operate on? | Time, Goals, Planning, Conversation, Knowledge |
| **Faculties** | What can the agent understand or interpret? | Temporal understanding, Language, Semantics |
| **Pipeline** | What happens, in what order? | User → Reasoning → Planning → Action → Result |
| **Infrastructure** | What technical machinery supports the system? | Persistence, storage, external services |

These are complementary views of the same system rather than competing structures.

---

## 2. System Structure

### Domains

A **Domain** is an area of responsibility or subject matter that the system operates on.

| Domain | Responsibility |
|---|---|
| Time | Durations, timeframes, dates, deadlines |
| Goals | Define and manage user goals |
| Planning | Turn goals into plans and revise them |
| Tasks | Represent concrete actions |
| Conversation | Interaction between user and agent |
| History | Preserve and retrieve past activity |
| Knowledge | Retrieve relevant user-provided knowledge |

`right_now` is currently represented inside the plan structure, but architecturally it should eventually represent an action or trigger rather than another time horizon.

### Faculties

A **Faculty** is a reusable area of agent understanding that is not tied to one Domain or one pipeline stage.

A Domain does not automatically get its own Faculty just because the agent needs to reason about it. Time, for example, is a Domain (what the system operates on); temporal understanding is the corresponding Faculty (the agent's reusable capability to interpret it — recognizing what "this weekend" means, comparing durations, etc.).

Temporal understanding and Math (quantitative reasoning, `backend/foundation/math.py`) are the two established Faculties. A Faculty is not limited to resolving ambiguous natural-language input — Time's own examples — it can equally be a fundamental, independently-existing domain of reasoning the agent needs a deterministic capability for, whether or not any single operation within it is itself ambiguous to resolve (see [[05-decisions]], "Faculty categorization" and its 2026-09-05 refinement). Math has no paired Domain the way Time does — nothing yet treats standalone quantities as first-class records the system operates on.

Other candidates include Language and Semantics, but a Faculty should still emerge through actual reuse, or represent a genuine, independently-existing reasoning domain — never created purely because a concept has a plausible name.

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

The Action stage is reasoning-only today — the agent doesn't yet perform external actions (creating a file, calling an API). Building that out is a parked idea: see [[06-development]] § Parking Lot.

---

## 3. Runtime Architecture

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

## 4. Architectural Principles

### Local-first

The user's device remains the authoritative copy of their data.

### Portable

User data should remain in open, human-readable formats where practical.

### Replaceable infrastructure

Cloud services, synchronization servers and external APIs are dependencies, not the source of truth.

### Privacy by architecture

Sensitive personal data should remain local where possible. If synchronization is introduced, it should preserve end-to-end encryption and user ownership.

### Start simple

Do not introduce databases, vector stores, services or distributed infrastructure until the current implementation creates a real, felt need for them.

> The app should be able to disappear without the user's history disappearing.

See [[05-decisions]] for the reasoning behind specific architectural decisions.

---

## 5. Architectural Components

### Time — Domain / Temporal understanding — Faculty

Time is a Domain (durations, timeframes, dates, deadlines); temporal understanding is the Faculty that provides deterministic interpretation of temporal expressions and durations.

It handles concepts such as:

- temporal expression matching
- duration resolution
- fixed goal timeframes
- relative duration comparison

Time interpretation is deliberately separated from LLM reasoning: **code decides, the model is told**.

The Faculty also owns backend's authoritative notion of current time (`now()`, `time_logic/current_time.py`) - the one place backend code reads the system clock, so a later extension (timezone, a frozen/mocked clock, etc.) only has to change there. Backend code that reads "now" for actual temporal reasoning or runtime decisions goes through it; a plain bookkeeping timestamp (e.g. `data_persistence.py`'s `created_at`) is Infrastructure, not temporal reasoning, and is left as a direct system-clock read. Frontend's own `Date.now()`/`new Date()` is separate browser runtime, untouched by this.

Seasons are a context-dependent, relative temporal concept, not a fixed global date range - which months "summer" names depends on hemisphere, and "this summer"/"next winter" are further relative to today. The Faculty owns season recognition and the rule for resolving one *given* a hemisphere; it does not default to one, and has no location/hemisphere concept of its own to supply it - a season is represented as recognized-but-unresolved until that context is available, the same honesty already applied to anything else not grounded in a real span.

Activity-specific interpretation of duration remains outside the established temporal-understanding Faculty for now.

### Math — Faculty

Math is a Faculty, not paired with a Domain — quantitative reasoning the agent can operate within, the same "code decides, the model is told" reasoning Time already established: a real numeric computation is always done deterministically in code, never guessed by the model.

First version (`backend/foundation/math.py`): the four basic arithmetic operations only — `add`/`subtract`/`multiply`/`divide`. A single flat module, not a package — matches the actual complexity of four functions; grows into more structure only if/when real need or reuse shows up (percentages, algebra, statistics, and an expression parser/evaluator are all explicitly not built yet).

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

See § Vision below for a concept above this pipeline, providing optional shared context for multiple Goals — distinct from Plan and not a new stage here.

### Vision — context shared across Goals

> Minimal representation implemented 2026-08-26 (see [[06-development]]). Naming and scope were exploratory before this date; both are now settled as described here. Not a Domain, not a Faculty, not a pipeline stage — see § Domains/Faculties above and "Architectural placement" below for why.

Vision represents the user's broader direction or desired future, optionally providing shared context for more than one Goal. It sits above the Goal → Plan → Action → Feedback → Replan loop, not inside it:

```text
Vision
 ↓
provides optional context to multiple Goals

Goal
 ↓
Plan
 ↓
Action
 ↓
Feedback
 ↺
```

Two things distinguish a real Vision from a renamed Plan — this distinction is the reason the concept was worth building at all, not just documenting:

- A single goal's own longer-horizon content ("write lyrics, book studio time" for "make a song") is scoped to *one* goal_id. That's Plan, at a broad timescale — already correctly Plan, not Vision, and unchanged by any of this.
- "Improve physical health and quality of life" informing *several independent* goals ("get visible abs," "improve cardio," "improve sleep") is scoped across goal_ids. Nothing represented this before 2026-08-26 — this is what Vision actually is.

**What's built.** A Vision is `{id, user_id, text, created_at}`, stored in its own file, `data/visions.json` — deliberately separate from `data/plans.json`, no relation between the two beyond a Goal record optionally carrying the id (see below). Created via the "Set a vision" form (`frontend/templates/vision/_vision_form.html`, `POST /vision`); listed and selectable when creating a goal. A Goal record may carry an optional `vision_id` (see `backend/infrastructure/data_persistence.py`'s `save_plan()`/`save_vision()`/`load_visions()`/`get_vision()`) — `None` is the normal case, not a gap to fill in. Set once at goal creation, carried forward unchanged across every later replan for that goal (same treatment as `frozen_duration`: a goal's Vision doesn't change just because its Plan does). In the interface, each Vision's Goals render nested inside it on the Vision page (`frontend/view_data/goal_overview.py`'s `group_goals_by_vision_id()`) — Active does not group goals by Vision.

**What's not built, on purpose.** No editing or deleting an existing Vision (create-only). No automatic goal generation from a Vision, and no Vision text supplied to the LLM yet at all — `generate_plan()`/`replan()` (`backend/goals/plan/planner.py`) both currently ignore a goal's `vision_id` entirely; their docstrings mark the exact spot where a short Vision summary could eventually be appended to the model's context, the same way `duration` already is. The relationship, if that's ever built, stays "Vision contextualizes Goals," never "Vision generates Goals."

**Why this shape.** [[05-decisions]] already considered essentially this need once before, from a different angle — "multiple life-domains (health/work/finance) reasoning about each other" — and concluded it should be lightweight context, not a relational join. This implementation follows that precedent: a small separate id+text store plus an optional foreign-key-style reference, the same pattern `goal_id` itself already uses, not a hierarchy. Duplicating the Vision's text directly onto every goal record (instead of a shared id) was rejected for the same reason goal identity moved off free-text years ago in this project's own history: two goals with independently-typed, slightly different vision text would silently fork into two visions instead of sharing one. See [[05-decisions]] for the full comparison of alternatives.

[[00-project-brief]] § Product Philosophy's "the life domain is secondary" remains a standing caution, not a blocker: Vision stays optional context a Goal can carry, never a required organizing layer every Goal must sit under.

**Architectural placement.** Not a Domain, Faculty, or pipeline stage. Per the Faculty rule applied elsewhere in this document (see [[05-decisions]], "Faculty categorization"), nothing here has demonstrated reusable understanding across Domains — Vision's storage functions live directly in `data_persistence.py` (Infrastructure: they move/store, they don't interpret), and its only consumers today are Goals/Planning.

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

A fact-checking capability built on top of this Domain — verifying a claim against retrieved sources rather than answering from training alone — is a parked idea, not yet designed: see [[06-development]] § Parking Lot.

### Memory — Domain

Memory is the agent's accumulated record of the user's goals, plans, activity and history.

It should remain local, portable and independently accessible from the application itself.

The exact long-term retrieval and organization model is intentionally not fixed yet. Whether a corresponding Faculty (e.g. how the agent selects, interprets, and relates past experience) eventually emerges is deliberately left open, not decided now.

See § Long-term architecture below for an exploratory hypothesis about a representation derived from this Domain's history, distinct from the raw record itself.

### World — Domain

World represents live external information and services the agent may eventually use when reasoning or acting — for example weather, calendars, maps and other external sources.

World is distinct from Knowledge:

- **Knowledge** = material the user has supplied
- **World** = live information from external systems

---

## 6. Long-Term Architecture

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

### Adaptive user representation and relational continuity (exploratory)

> Hypothesis under exploration as of 2026-08-26, not a design commitment. Nothing described in this subsection exists in the codebase; see [[04-current-state]] for what's actually built.

Beyond an LLM, prompts, and memory as retrieval of past conversation, the agent could in principle maintain a small, persistent representation of the user that is shaped and updated by experience, rather than only stored and looked up:

```text
experience
    ↓
memory / raw events
    ↓
adaptive internal representation
    ↓
expectation
    ↓
new observation
    ↓
discrepancy
    ↓
updated internal state
    ↓
changed future behaviour
```

This separates two things that retrieval alone does not distinguish:

- **Raw memory** — what happened: individual events, as a record. This is what § Memory above already describes, and what `memory/` is a scaffold for.
- **Adaptive representation** — what has been generalized from what happened: a compact, updated statistic (e.g. an expected rate, or a belief with a confidence) that is shaped by every observation and used to interpret the next one, instead of being re-derived from raw records each time.

The property that matters is a native notion of *expectation* and *discrepancy*. Retrieval finds records similar to a query; on its own, it does not produce "this differs from what has been observed for this person" as a first-class signal — that requires some form of persistent, incrementally updated state.

Not a requirement to use a neural network. The open question is not "how is a neural network added to the agent" but "how could the agent's internal representation of the user actually change through experience, at all." A small neural network is one possible future implementation of such a representation. Given a single-user, low-volume, non-stationary source of data (see [[04-current-state]]), a simpler mechanism — an exponential moving average, Bayesian updating, or another lightweight statistical estimator — is more likely to be the right starting point, for the same reason [[05-decisions]] already gives for keeping other true/false judgments (e.g. outcome classification) deterministic rather than model-based: interpretability, and resistance to acting on too little data, matter more here than representational capacity. A mechanism like this would sit alongside, not replace, deterministic logic and LLM reasoning — the same layering already used elsewhere: code decides what it can, a lightweight model estimates what depends on accumulated personal history, the LLM handles language.

Whatever the mechanism, the representation should remain derivable from the raw event log, not the only record of it — Memory stays the source of truth (see § Architectural principles, "Local-first" and "Portable"); an adaptive representation is a rebuildable derived state, not a replacement for it.

**Relational continuity.** A related hypothesis: continuous recognition of the user, and behavior that visibly reflects accumulated history with them specifically, may be what gives an agent relational continuity over time — not a simulated personality or emotional behavior. The distinction drawn: the aim is for the user to experience "this is the same entity I've dealt with before," not "this is a person" — recognition and consistency, not anthropomorphism. If built, this would show up as the agent's behavior visibly depending on what it has previously observed about this specific user (e.g. a plan revision or a check-in shaped by their own prior pattern, rather than a generic response) — not as a claim the agent makes about itself.

**Terminology note.** "Primal intelligence" is used here as an informal, exploratory working term for a question — roughly, what is the smallest set of mechanisms giving an agent its own goal-directed, adaptive behavior, before relying on progressively larger models and tools — not as an established technical term, a proposed Domain/Faculty name, or a claim about the system's implementation. Persistent internal state, recognition, expectation, discrepancy-detection, and adaptive behavior do not require or imply subjective experience; nothing in this subsection is a claim about machine consciousness.

**Architectural placement.** None of this is placed as a Domain or Faculty. Per the existing rule for what qualifies as a Faculty (see [[05-decisions]], "Faculty categorization"), a Faculty must be reusable understanding demonstrated across more than one Domain, not created because a concept has a plausible name. Today, an adaptive user representation would only be relevant to Planning and Goals. If built, it belongs as a capability internal to those Domains, not a new Domain or Faculty — unless a similar need for it later appears in another Domain (e.g. Knowledge or Conversation), at which point it would meet the project's own bar for becoming one.

See § Parking Lot in [[06-development]] for two smaller, related interface ideas explored alongside this: a minimal visual identity for the agent, and a "notice" interaction surface for a detected discrepancy.

### Representation, signals, and evaluation (exploratory)

> Hypothesis under exploration as of 2026-09-05, not a design commitment. Nothing described in this subsection exists in the codebase; see [[04-current-state]] for what's actually built. Related to, but distinct from, the adaptive-representation hypothesis above — that subsection asks how the agent's internal model of the user could change through experience; this one asks what the raw material for such a model — a "signal" — actually is, and what it isn't.

**Representation is not meaning.** A symbol or number is a representation; what it stands for is a separate, context-dependent question. `0`–`9` are symbols used to represent quantities in the decimal system. `1` can represent the number one. In a specific structural context, `1` can instead represent "first." If a system adopts the convention that weekdays are numbered Monday = 1, then `1 → Monday` — but this does not mean the number `1` *itself* means Monday. It is a mapping between a representation/structure and a concept, defined for a particular context. The same distinction applies to `+1 → positive`, `0 → neutral`, `-1 → negative`: arithmetic itself does not say `+1` means "good" — that is a semantic convention a system defines for a given domain, exactly as `1 → Monday` is a convention for calendar structure, not a mathematical fact. The question to ask of any such symbol is always *what does this represent, in this context* — the same representation can carry different meaning in different domains, and conflating them (treating a calendar mapping and an evaluative mapping as "the same kind of thing" because both happen to use small integers) would be a mistake.

**Evaluation as a scale.** The same idea extends from a binary good/bad to a continuous scale, e.g. `-10 ←── -1 ── 0 ── +1 ── +10`, where the magnitude represents the strength of an evaluation (`-10` very negative, `0` neutral, `+5` more positive than `+1`, `+10` very positive). `+8` does not mean "objectively better" than `+5` in any absolute sense — it means that, within whatever evaluation model produced these numbers, one thing was rated more positively than the other. This range is illustrative of the idea of graded evaluation, not a proposed scoring architecture, storage format, or algorithm.

**Signal types are not interchangeable.** Several different kinds of signal could exist, and collapsing them because they might all eventually be represented numerically would lose real distinctions:

- **Preference** — what the user likes or dislikes ("I like gaming").
- **Agent feedback** — how the user evaluates the agent's own behavior or the collaboration itself ("I like how we're planning now"; "this got too rigid"; "I wish we had more of X").
- **Activity feedback** — how the user experienced or evaluated a specific activity ("the workout was actually fun"; "I hated this workout").
- **Behavior signal** — what the user actually did (a workout was planned → the workout happened, or didn't).
- **Outcome signal** — what actually resulted from an action, plan, or decision ("this way of planning led to more follow-through"; "this plan worked poorly").

**A signal needs semantic context.** A bare `-1` means almost nothing on its own. A tentative structure: `signal → type → object → context → evaluation → time`. `-1 + preference + vegetables` is a different thing from `-1 + agent feedback + planning style`, which is different again from `-1 + behavior signal + workout follow-through`, and different again from `-1 + outcome signal + a specific plan`. The number can be identical; the meaning differs because the signal's semantic context differs.

**One data point is not a pattern.** A single signal should not automatically become a strong conclusion. Over time the agent could accumulate `observation → evaluation → context → more observations → possible pattern` — e.g. `large task → low follow-through`, repeated across enough comparable, relevant situations that it starts to look like a relationship worth taking into account. But a pattern is not the same as a certain truth, no matter how many times it repeats; it stays a candidate relationship, open to revision by the next observation.

**A tentative overall chain** (illustrative, not an adopted pipeline or finished architecture):

```text
observation
    ↓
semantic interpretation
    ↓
signal type
    ↓
evaluation
    ↓
context
    ↓
accumulation
    ↓
pattern / relationship
    ↓
possible learning
    ↓
future behavior
```

**Preferences in planning.** If a user likes gaming more than exercise, that could be represented as, for example, `gaming → +8` and `exercise → +5` — but this would not mean "the agent should maximize gaming." It would only mean gaming carries a higher preference value in this particular user's model. Exercise can simultaneously carry other preferences, goal relationships, health/wellbeing relationships, long-term value, and its own outcomes — so a future planning step would potentially need to weigh `preferences + goals + constraints + activities + expected outcomes + long-term value` together, not act on a single preference number in isolation. Relatedly, planning does not have to be experienced as "a strict list of things I must do" — it could instead be a way of designing a day the user actually wants to live. A day shaped as `work → exercise → gaming`, where gaming is something genuinely looked forward to, is one illustration of using a user's own preferences as a positive planning component rather than treating a preferred activity as something to be minimized because it isn't "productive." This is not a claim about how everyone should plan their life — it is the narrower idea that the agent could use a user's own preferences to make plans that feel more attractive and motivating to that specific user.

**Relation to relational continuity (above).** Agent feedback specifically — how the user reacts to the collaboration itself, not to an activity or outcome — is a distinct signal type from the others listed here, and plausibly the one most directly relevant to the relational-continuity hypothesis above: a relationship that develops not just from remembering facts about the user, but from noticing how the user responds to activities, to what actually happens, and to the agent's own suggestions and way of working, and letting that shape future behavior. The difference drawn earlier in this document — storing information versus understanding relationships between information and using them later — applies here too.

**Architectural placement.** None of this is a Domain, Faculty, class, storage model, or algorithm. No `Signal`, `Feedback`, `Semantics`, or `Preference` class is proposed. No database or persistence model is decided. No scoring, learning, or pattern-detection mechanism is specified or implemented anywhere in the codebase. The `-10`–`+10` range above is an illustration of graded evaluation, not an adopted scale. None of this is a model of human psychology in general — it is a set of distinctions (representation vs. meaning, signal type, single point vs. pattern) that would need to hold if this kind of user understanding is ever built, per the same Faculty bar already applied above (see [[05-decisions]], "Faculty categorization").

### World knowledge, retrieval, and reasoning (exploratory)

> Hypothesis under exploration as of 2026-09-05, not a design commitment. Nothing described in this subsection exists in the codebase; see [[04-current-state]] for what's actually built. Direct continuation of "Representation, signals, and evaluation" above — that subsection asked what a signal about the user means; this one asks the same representation-vs-meaning question about knowledge of the world the user exists in.

**Two kinds of knowledge.** The agent appears to need access to at least two fundamentally different kinds of knowledge. **User-specific knowledge** — information about the concrete user: preferences, experience, past events, activity and behavior, feedback on the agent's own behavior, and relationships between these. **World knowledge** — knowledge about the world outside the user: history, religion, psychology, philosophy, culture, society, science, language, literature, art, people, places, and other areas relevant to understanding people and the world. Whether each of these areas becomes its own knowledge domain, whether they form one larger world-knowledge system, or something else, is explicitly not decided here.

**World knowledge as more than isolated facts.** `World War II → 1939–1945` is a fact. A richer knowledge system could also hold relationships — World War II to geopolitics, nationalism, ideology, economics, technology, human suffering, migration, political change, post-war society; psychology to motivation, emotion, cognition, behavior, relationships, habits; history to events, people, causes, consequences, cultural and political change. This doesn't mean the agent needs an explicit graph system now — the point is only that knowledge becomes far more useful when concepts can be related to one another, not stored as disconnected entries.

**Why history, psychology, relationships, religion, and culture matter here.** An agent trying to understand a person can't necessarily do it just by knowing `user likes gaming` — it may also need world knowledge about what gaming actually involves: leisure, motivation, competition, social interaction, reward, entertainment. `user → relationship → another person` could similarly become more understandable through knowledge of friendship, family, trust, conflict, communication, attachment, social behavior. A user's reference to a historical, cultural, or religious thing can be hard to interpret without relevant world knowledge either. None of this means the agent should psychoanalyze the user or draw firm conclusions — world knowledge supplies context, not automatic truth about the person.

**Religion as a concrete example: the Bible and the Quran.** Both can be viewed as culturally and historically significant knowledge sources, holding large amounts of information about human experience, morality, family, love, conflict, guilt, hope, death, justice, power, society, ritual, and humanity's relationship to the divine. The point is not to treat either text as objective truth, or to rank one religion above another — it's that understanding human culture may benefit from understanding what people have actually believed, written about, lived by, and built societies around. Drawing on more than one tradition (rather than only one) also reduces the risk of a world model shaped by a single cultural or religious lens. This requires keeping `source says X` (knowledge about a source) distinct from `X is objectively true` (a claim) — `Bible → contains a particular view of morality` is knowledge about a source; `this moral principle is good` is a separate semantic/evaluative judgment, and the two must not be conflated. The same idea extends well beyond religious texts, to historical books, philosophical texts, psychological literature, scientific publications, legal texts, literature, and other cultural or documentary sources that help the agent understand the world — the point is not any one book or religion, but breadth of access to human knowledge and perspectives. Neither text (nor any other single source) is proposed as a special architecture component here.

**Retrieval (RAG) as one possible mechanism.** A possible future shape: `source material → representation → retrieval → relevant context → LLM reasoning`. World knowledge could live as data outside the Python code — a book, historical source, research paper, or religious text as a knowledge source the agent retrieves relevant parts from when needed. A central point: **knowledge access is not the same thing as reasoning.** Retrieval could give the agent access to relevant information; it would not itself be what performs the reasoning over that information — that stays the job of the LLM or a deterministic capability, same as elsewhere in this document.

**World knowledge alongside Time and Math.** World knowledge: `9/11 → 2001-09-11`. Time: `now() → current date`. Temporal reasoning: `2001-09-11 → approximately 25 years ago`. Retrieval doesn't perform that temporal computation — it supplies the fact Time can work with. A world-knowledge fact about a historical event's effect on a population could, similarly, be something Math computes a difference, percentage, or ratio over. This illustrates knowledge access and deterministic reasoning as different, cooperating capacities — the same relationship Time and Math already have with the rest of the system.

**The same representation-vs-meaning distinction applies here.** Recall from the subsection above: representation ≠ meaning, and `+1`/`0`/`-1` only mean something through context and semantics. The same holds for knowledge: `"Monday"` is a temporal-concept representation, and `"9/11 occurred on 2001-09-11"` is a world-knowledge representation — neither is reality or meaning itself, both are representations the agent could use for further reasoning. Two still-conceptual chains, side by side: `world knowledge → representation → retrieval → context → reasoning`, and (from the previous subsection) `user observation → interpretation → signal → context → accumulation → relationship/pattern → future behavior`. Neither is an implemented pipeline.

**Why this matters for a personal agent.** A personal agent doesn't only need to know things *about* the user — it may also benefit from a broader picture of the world the user exists in. A user might reference a historical event, a religious idea, a psychological experience, a philosophical problem, a relationship between people, or a cultural reference; world knowledge could help the agent understand the context around what the user actually said. This suggests two chains that could meet in the agent's reasoning: `world knowledge → context → understanding → reasoning`, alongside `user experience → signal → context → relationship → future behavior`.

**A cautious link to human experience.** Connects to the earlier discussion of a synthetic understanding of human feeling — not a claim that the agent should "feel." The hypothesis is only that `world knowledge + user knowledge + signals + context + relationships`, combined, could let the agent build an increasingly rich representation of human experience — potentially enabling it to represent and reason over things like liking/disliking, joy/frustration, motivation, difficulty, preference, fear, belonging, loss, hope, satisfaction, and meaning, and relationships between activities and experiences — without claiming any of this is the same as subjective human experience.

**From storage to understanding.** `store information → retrieve information → connect concepts → interpret context → reason over relationships → use the result in future interaction`. A possible transition from a system that only has memory/knowledge to one that begins building a relational model of the world and the user — the same direction the previous subsection already points toward.

**Knowledge as raw material for reasoning, not just something to store.** A further refinement of "knowledge access is not the same thing as reasoning" above: the agent may need knowledge not because it should hold a large knowledge base, but because knowledge is raw material for reasoning. It isn't enough to think of `Bible → document`, `Quran → document`, `WWII → document`, `Darwin → document` as isolated retrieval targets. The more interesting capability appears once these knowledge objects can be related to each other, and to the agent's other capabilities — Time, Math, context, relationships.

**Temporal distance as something to reason about, not tag.** Rather than hardcoded rules like `Bible = abstract` or `WWII = concrete`, the agent could in principle derive why temporal distance matters:

```text
World knowledge: Bible → ancient text → roughly 2000 years ago
Time: now → 2026
Temporal reasoning: ~2000 years of distance
    → many human generations separate the present from the original period
    → no living human has direct personal experience of that period
    → the relationship to the material is historical/cultural/religious, not direct lived experience

World knowledge: WWII → 1939–1945
Time: now → 2026
Temporal reasoning: ~80 years of distance
    → some people who directly experienced the events may still be alive
    → children and grandchildren of participants are alive
    → institutions, families, and cultural memory remain directly connected to present society

World knowledge: an event → yesterday
Time: now → today
Temporal reasoning: very small distance
    → direct contemporary experience is possible
    → the event belongs directly to the present context
```

The point isn't "old = abstract, new = concrete" — it's that temporal distance changes the relationship humans can have to an event, person, idea, or source, and that this is something the agent could potentially reason toward rather than have handed to it as a label.

**Direct experience vs. inherited knowledge.** An important precision: this isn't a claim that people can't relate to something because it's 2000 years old. People can have strong emotional, cultural, religious, philosophical, or identity-based relationships to very old stories and texts — a person can have a deep personal relationship to the Bible or the Quran without personal experience of the period the texts describe. The relevant distinction is `direct lived experience` versus `indirect / inherited / cultural / historical relationship` — temporal reasoning can supply context here without dictating what a person should feel or believe about it.

**Extending the same idea to history, biology, psychology, and relationships.** History can be understood in relation to time, generations, causes, consequences, institutions, and cultural memory. Biology can give the agent a sense of human lifespan, generations, reproduction, evolution, and the difference between biological and cultural timescales. Psychology can give context around motivation, emotion, cognition, behavior, habits, and relationships. Knowledge of human relationships can give context around family, friendship, trust, conflict, communication, and belonging. As before, none of this means psychoanalyzing the user or drawing firm conclusions — it supplies context, not automatic truth about the person.

**Darwin as a worked example of knowledge + Time + Math combined.** World knowledge: `Darwin → evolutionary biology`, `Darwin → 19th-century scientific history`, `human lifespan → decades`. Time: `1859 → 2026`. Math: `2026 - 1859 ≈ 167 years`, and `167 ÷ ~25–30 ≈ ~5–7 generations`. The interesting part isn't retrieving `Darwin → 1859` alone — it's combining knowledge areas to produce a new, derived relation: `historical distance → several human generations`. This is a concrete illustration of knowledge being used as raw material for reasoning, rather than an isolated fact.

The more extreme case makes the same point: a historical or religious source roughly 2000 years old, divided by a human generation of roughly 25–30 years, derives to roughly 67–80 generations separating the present from that period — usable to reason about the difference between direct experience and cultural/historical transmission. The derivation itself is the interesting part; the conclusion should not be hardcoded as a label.

**The agent's own position in time.** The agent could in principle represent its own temporal position (`agent existence → 2026, present`) alongside world knowledge (`WWII → 1939–1945`, `Bible → ancient history`, `Quran → 7th century`, `Darwin → 19th century`), and so distinguish `knowledge about an event` from `experience of an event` — knowing a great deal about WWII, or about the Bible or Quran, without treating itself as having been present for any of it. This isn't a finished self-awareness system; it's a conceptual consequence of combining an own temporal position, world knowledge, and Time.

**Three cooperating capacities, not three finished modules.** Knowledge (what happened), Time (when it happened, and how far that is from now), and relational reasoning (what that difference in time, knowledge, experience, context, and relevance actually means) illustrate how different capacities could contribute to one reasoning process, without being three system modules in their own right. Combining a world-knowledge fact (`WWII → 1939–1945`), Time (`now → 2026`), Math (`~80 years`), and biological knowledge (`human lifespan → decades`) could derive that roughly several human generations separate the event from the present, that some direct witnesses may still be alive, and that its historical consequences can remain directly connected to present society — not because Math or Time alone "understands" any of this, but because reasoning can arise through their combination with knowledge.

**From tagging to derivation.** A materially different point from giving the agent fixed metadata like `Bible → abstract` or `WWII → concrete` (a predefined classification): `knowledge → temporal information → biological information → mathematical calculation → relationships → derived context → reasoning`. Not just tagging, but derivation — the agent potentially discovering a relevant property because it can combine underlying knowledge, which is a more interesting form of capability than an object simply carrying the correct label.

**Tying back to representation, signals, and evaluation.** World knowledge can supply information about objects and context; Time can supply temporal structure; Math can supply quantitative structure; signals can represent the user's own evaluations and experience; relational reasoning could potentially connect all of this. Sketched together, still only as a conceptual model under exploration, not an architecture or pipeline:

```text
world knowledge + user knowledge + representation + semantics/context
    + signals + Time + Math + relationships
        ↓
    reasoning
```

**Knowledge becomes useful through relation, not just retrieval.** Alongside "knowledge access is not the same thing as reasoning," the reverse matters too: knowledge becomes useful for reasoning when the agent can relate retrieved information to other known concepts and to deterministic operations. Sketched as capabilities rather than components — Time could contribute temporal position, duration, distance between events, and before/after or relative-time judgments; Math could contribute addition/subtraction, ratios, percentages, averages, and other quantitative comparison; world knowledge could contribute facts, concepts, and historical, biological, cultural, psychological, religious, and philosophical information. None of these lists is a proposed API — they name what each capacity could plausibly supply toward one shared reasoning step, as already illustrated by the Darwin and 2000-year examples above.

**Relational reasoning, named.** The relationships between knowledge objects, not the isolated facts themselves, are what this subsection keeps returning to: `historical event → temporal distance → human generations → biological context → cultural transmission → present-day relevance` is the kind of chain meant by the "relational model of the world and the user" mentioned above — not a knowledge graph to be implemented now, just the observation that relationships between knowledge objects appear central to this kind of reasoning. A shorter, more general version of the same idea: `fact → context → relationship → comparison → calculation → interpretation → reasoning` — again, not a defined pipeline, only a way of illustrating the direction being explored.

**Left open, deliberately.** Whether RAG is a Faculty, whether "Knowledge" is a Faculty, whether RAG is Infrastructure, whether world knowledge and retrieval should be separate layers, whether a future Semantics Faculty should exist, whether "relational reasoning" is a Faculty, whether a knowledge graph is necessary, and whether areas like psychology or history need to be their own Faculties are all explicitly undecided here — as is any form of self-awareness beyond representing an own temporal position. No file, class, database, embedding, or API is proposed or built. What this subsection identifies is only that access to world knowledge, personal knowledge, representation, semantics, signals, and relational reasoning appear to be closely connected — that world knowledge may be valuable not merely as stored information but as raw material combinable with Time, Math, user knowledge, context, and relationships to support reasoning, and that temporal distance, biological constraints, human generations, cultural transmission, and the agent's own temporal position are concrete examples of things that could potentially be derived rather than hardcoded. Per the same Faculty bar already applied above (see [[05-decisions]], "Faculty categorization"), none of these is elevated to one merely for having a plausible name.

---

## See also

- [[02-product]]
- [[04-current-state]]
- [[05-decisions]]
- [[06-development]]
