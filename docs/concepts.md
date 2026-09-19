# Concepts

> **Restructuring note (2026-09-11):** renamed from `07-future-ideas.md`, then again from `07-concepts.md` to this, unnumbered — deliberately outside the `00`-`06` skeleton (a closed, designed set of document roles) and alongside `v4-migration-decision.md`/`planning-model.md` instead, the vault's existing category for a standalone, topic-specific, ever-growing document. Restructured into `1. → i. → a.` sections (see `../global-standards/_CONTENT_HIERARCHY.md`), grouped by actual topic rather than by where the content originally came from — so it can be read into directly, not only read start to finish. Originally consolidated from `current/docs/03-architecture.md § 6 Long-Term Architecture` and this vault's own `06-development.md § 5 Parking Lot` — see [[06-development]] for that earlier move. Cross-references inside these entries to "§ Time above", "§ Math above", "§ Planning above", "§ Architectural principles", and "§ System structure" point to sections of the settled-architecture document `docs/03-architecture.md`, still to be written fresh for v4 — not part of this document. `[[04-current-state]]`, referenced throughout, doesn't resolve yet for the same reason.

> Speculation — not decided, not built, and not a committed roadmap. See `../COLLABORATION.md`'s doc-role table: "What might happen? → Not decided, not built." Ranges from concrete, scoped feature ideas to open, unresolved conceptual reflection — both belong here side by side; neither is a promise.

> **Vocabulary:** entries below often say Goal / Plan / Planning. For today's product names (Project, canvas, engine), see [[04-current-state]] § Vocabulary — speculation here keeps the older words on purpose.

## Contents

1. Architectural context
   i. The long-term loop diagram (historical, pre-Node-model)
2. Understanding the user
   i. Adaptive user representation and relational continuity
   ii. Representation, signals, and evaluation
3. Understanding the world and agent state
   i. World knowledge, retrieval, and reasoning
   ii. Agent state as composable faculties
   iii. A candidate fifth foundational area (name undecided)
4. Planning and product features
   i. Plan as an ordered step list
   ii. Recognize a real, already-happened start time
   iii. Export/share a goal's plan as a document
   iv. Fact-checking as a layer on the future Knowledge/RAG room
   v. Semantic understanding of time, not just numeric duration
   vi. The agent actually doing things, not just explaining how
   vii. Goal ≠ Plan: the goal stays stable, the plan is revisable
   viii. Reflection / progress summaries
   ix. Practices, not projects: a recurring commitment has no shape yet
   x. A plan can only be regenerated, never edited
   xi. Vision as what makes an activity legitimate, not a larger goal
5. Interface, platform, and delivery
   i. Multi-device sync via end-to-end encryption
   ii. Calendar integration
   iii. Push notifications / proactive outreach
   iv. iOS app with Swift/SwiftUI
   v. Android / cross-platform
   vi. Duolingo-style habit/identity mechanics
   vii. Low-friction interaction
   viii. Web interface translating portable data into a UI
   ix. Aggregation / world-data capability
   x. Minimal, stable visual identity for the agent
   xi. "Notice" as a possible interface for a detected discrepancy
6. See also

## 1. Architectural context

### i. The long-term loop diagram (historical, pre-Node-model)

This is a pre-`v4-migration-decision.md` sketch, kept as a record of the earlier framing, not a current target:

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

It does not reflect what the project is actually building toward now: a single undifferentiated "Reasoning" stage, not the Node/Module/Faculty separation (Interface → Parser → Decision, each a narrow role; Module Library as optional internal tools; Faculties as deterministic capabilities) the project has since actually developed — see `docs/03-architecture.md` for the real direction. Future interfaces (web, iOS, Android) should still sit above the same backend and portable data rather than defining the underlying architecture; future synchronization should still preserve the local-first principle (devices authoritative, sync infrastructure replaceable) — those two framing points outlive the diagram itself. None of this is built as part of the current MVP. See [[02-product]] and [[06-development]].

## 2. Understanding the user

### i. Adaptive user representation and relational continuity

Explored 2026-08-26. Beyond an LLM, prompts, and memory as retrieval of past conversation, the agent could in principle maintain a small, persistent representation of the user that is shaped and updated by experience, rather than only stored and looked up:

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

This separates two things that retrieval alone does not distinguish: **raw memory** (what happened — individual events, as a record) from an **adaptive representation** (what has been generalized from what happened — a compact, updated statistic shaped by every observation and used to interpret the next one, instead of being re-derived from raw records each time). The property that matters is a native notion of *expectation* and *discrepancy* — retrieval finds records similar to a query, but doesn't on its own produce "this differs from what has been observed for this person" as a first-class signal; that needs some form of persistent, incrementally updated state.

Not a requirement to use a neural network. The open question is not "how is a neural network added" but "how could the agent's internal representation of the user actually change through experience, at all." Given a single-user, low-volume, non-stationary data source, a simpler mechanism (an exponential moving average, Bayesian updating, another lightweight statistical estimator) is more likely the right starting point than a neural network — for the same reason [[05-decisions]] already gives for keeping other true/false judgments deterministic rather than model-based: interpretability, and resistance to acting on too little data, matter more here than representational capacity. Whatever the mechanism, the representation should remain derivable from the raw event log, not the only record of it — Memory stays the source of truth; an adaptive representation is a rebuildable derived state, not a replacement for it.

**Relational continuity**, a related hypothesis: continuous recognition of the user, and behavior that visibly reflects accumulated history with them specifically, may be what gives an agent relational continuity over time — not a simulated personality or emotional behavior. The aim is for the user to experience "this is the same entity I've dealt with before," not "this is a person." If built, this would show up as the agent's behavior visibly depending on what it has previously observed about this specific user — not as a claim the agent makes about itself.

"Primal intelligence" is used only as an informal working term for a question — roughly, what is the smallest set of mechanisms giving an agent its own goal-directed, adaptive behavior — not an established term, a proposed name, or a claim about the system's implementation. Persistent internal state, recognition, expectation, discrepancy-detection, and adaptive behavior do not require or imply subjective experience; none of this is a claim about machine consciousness.

**Placement:** none of this is a Domain or Faculty. Per the Faculty rule ([[05-decisions]], "Faculty categorization"), a Faculty needs reusable understanding demonstrated across more than one Domain — today this would only be relevant to Planning and Goals, so if built it belongs inside those Domains, not as a new one, unless a similar need later appears elsewhere. See § 5.x below for two related interface ideas explored alongside this: a minimal visual identity for the agent, and a "notice" surface for a detected discrepancy.

### ii. Representation, signals, and evaluation

Explored 2026-09-05. A representation is not its meaning — `0`–`9` are symbols; what they stand for is a separate, context-dependent question. `1 → Monday` is a convention for calendar structure, not a mathematical fact about the number 1, the same way `+1 → positive` is a semantic convention a system defines for a domain, not something arithmetic itself says. The same idea extends to a continuous evaluation scale, e.g. `-10` to `+10` — illustrative of graded evaluation, not a proposed scoring architecture.

Several kinds of signal exist and shouldn't collapse into one just because they might all end up numeric: **preference** (what the user likes/dislikes), **agent feedback** (how the user evaluates the agent/collaboration itself), **activity feedback** (how they experienced a specific activity), **behavior signal** (what they actually did), **outcome signal** (what actually resulted). A bare `-1` means almost nothing alone — a tentative structure: `signal → type → object → context → evaluation → time`. And one data point is not a pattern: a single signal shouldn't become a strong conclusion; a pattern (`large task → low follow-through`, repeated across comparable situations) stays a candidate relationship, open to revision by the next observation, no matter how many times it repeats.

Illustrative, not adopted: `observation → semantic interpretation → signal type → evaluation → context → accumulation → pattern/relationship → possible learning → future behavior`.

**Preferences in planning:** if a user likes gaming more than exercise (`gaming → +8`, `exercise → +5`), that wouldn't mean "maximize gaming" — only that gaming carries a higher preference value in this user's model, to be weighed alongside goals, constraints, and expected outcomes, not acted on in isolation. Planning doesn't have to read as "a strict list of things I must do" — it could be a way of designing a day the user actually wants to live, using their own preferences as a positive planning component rather than treating a preferred activity as something to minimize for not being "productive."

Agent feedback specifically — how the user reacts to the collaboration itself — is plausibly the signal type most directly relevant to relational continuity above: a relationship that develops from noticing how the user responds to the agent's own suggestions and way of working, not just from remembering facts about them.

**Placement:** none of this is a Domain, Faculty, class, storage model, or algorithm. No `Signal`/`Feedback`/`Semantics`/`Preference` class, database, or scoring/learning mechanism is proposed or built anywhere. Not a model of human psychology in general — a set of distinctions (representation vs. meaning, signal type, single point vs. pattern) that would need to hold if this kind of user understanding is ever built.

## 3. Understanding the world and agent state

### i. World knowledge, retrieval, and reasoning

Explored 2026-09-05, direct continuation of § 2.ii above — that one asks what a signal about the user means; this one asks the same representation-vs-meaning question about knowledge of the world the user exists in.

The agent appears to need at least two fundamentally different kinds of knowledge: **user-specific** (preferences, experience, past events, behavior, feedback) and **world** (history, religion, psychology, philosophy, culture, society, science, and other areas relevant to understanding people and the world). Whether these become separate knowledge domains or one larger system is undecided.

World knowledge is more than isolated facts (`World War II → 1939–1945`) — a richer system could hold relationships (WWII to geopolitics, nationalism, economics, human suffering). This doesn't mean an explicit graph system is needed now — only that knowledge becomes more useful when concepts relate to each other rather than sitting as disconnected entries. History, psychology, relationships, religion, and culture matter here because understanding a person by knowing `user likes gaming` benefits from world knowledge about what gaming actually involves — leisure, motivation, competition, reward; none of this means psychoanalyzing the user, only supplying context.

**Religion as a concrete example — the Bible and the Quran:** both viewed as culturally/historically significant sources holding material about morality, family, conflict, guilt, hope, and humanity's relationship to the divine — not treated as objective truth, and no ranking of one religion above another. Drawing on more than one tradition reduces the risk of a world model shaped by a single cultural or religious lens. This requires keeping `source says X` (knowledge about a source) distinct from `X is objectively true` (a claim) — `Bible → contains a particular view of morality` is knowledge about a source; `this moral principle is good` is a separate, unconflated judgment. The same treatment extends to historical, philosophical, and psychological sources, not only religious ones — no single book or religion is proposed as a special component.

**Retrieval (RAG)** is one possible mechanism: `source material → representation → retrieval → relevant context → LLM reasoning`. Central point: knowledge access is not the same thing as reasoning — retrieval gives access to information, it doesn't perform the reasoning over it, that stays the LLM's or a deterministic capability's job.

**Worked example — Darwin, knowledge + Time + Math combined:** `Darwin → evolutionary biology`, `1859 → 2026`, `2026 - 1859 ≈ 167 years`, `167 ÷ ~25–30 ≈ ~5–7 generations`. The interesting part isn't retrieving `Darwin → 1859` alone — it's combining knowledge areas into a derived relation: historical distance → several human generations. A more extreme case (a ~2000-year-old source, divided by a ~25–30 year generation) derives to roughly 67–80 generations, usable to reason about direct experience vs. cultural/historical transmission — the derivation is the interesting part, not a hardcoded label. Important precision: this isn't a claim people can't relate to something 2000 years old — a person can have a deep personal relationship to an ancient text without personal experience of its period; the relevant distinction is `direct lived experience` vs. `indirect/inherited/cultural relationship`, and temporal reasoning can supply context without dictating what someone should feel or believe.

The agent could in principle represent its own temporal position (`agent existence → 2026`) alongside world knowledge, distinguishing `knowledge about an event` from `experience of an event` — not a finished self-awareness system, a conceptual consequence of combining temporal position, world knowledge, and Time.

**Left open, deliberately:** whether RAG is a Faculty, whether "Knowledge" is a Faculty, whether RAG is Infrastructure, whether a future Semantics Faculty should exist, whether "relational reasoning" is a Faculty, whether a knowledge graph is necessary, whether psychology or history need to be their own Faculties, and any form of self-awareness beyond representing an own temporal position — all explicitly undecided. No file, class, database, embedding, or API is proposed or built.

### ii. Agent state as composable faculties

Explored 2026-09-06, a general frame around § 3.i and § 2 above — how knowledge, time, relationships, causality, and goals could eventually operate together as one system. The agent's state at a moment, `A_t`, could be thought of as a tuple of separate structures rather than one flat store — e.g. `A_t = (K, T, R, C, G, ...)`: `K` a knowledge universe, `T` a time structure, `R` a relational structure, `C` a causal structure, `G` goals. Not a proposed data model or a claim these five specifically exist — the idea is that different kinds of structure could each need their own representation and be reasoned over together rather than folded into one blob. `G` already has a concrete anchor in the Goals Domain; `K` is the subject of § 3.i above; `R` overlaps § 2.i above; `C` and a richer `T` than what's built today have no existing counterpart.

A richer `T` could represent intervals, before/after ordering, simultaneity, and change over time as first-class structure, not only a single "what time is it" value. The faculties aren't necessarily isolated: `K + T` could mean knowledge structured by when it applies, `K + T + R + C + G` could give planning a much richer basis than any one alone — not that these combinations exist or are being built, only that the long-term direction is toward structures that can operate together.

A related idea: the LLM might not need to be the entirety of the agent's reasoning — `K/T/R/C/G → structured representations → symbolic/computational operations → structured state → LLM → interpretation/ambiguity/hypothesis/language → new retrieval → updated structures`, continuing the "code decides, the model is told" split already established for Time and Math, generalized further. Candidate primitive operations (`retrieve()`, `locate()`, `compare()`, `infer()`, `predict()`, `evaluate()`, `plan()`, `act()`, `update()`, `replan()`) illustrate a possible vocabulary, not a proposed API.

This connects to what's built: Goal → Plan → Action → Feedback → Replan is already, in effect, an `S_{t+1} = F(S_t, I_t)` step for the plan's own state. The idea explored here is that `S_t` could eventually become far richer, approaching the `A_t` framing above — not that today's model is wrong or needs to change to get there.

**Placement:** none of this is a Domain, Faculty, class, storage format, or algorithm. No knowledge graph, temporal database, causal-reasoning engine, or symbolic-reasoning engine is proposed or built. The existing Goal → Plan → Action → Feedback → Replan model is unchanged and continues to be developed pragmatically, independent of whether any of this is ever built.

### iii. A candidate fifth foundational area: human experience, self, and normative reasoning (name undecided)

Explored 2026-09-06, builds on § 3.ii above (Time, Math, and two new candidates — Architecture, Computer Science — as "foundational faculties": formal modes of orienting toward reality, not bodies of knowledge) and asks whether a fifth, peer-level area belongs alongside them. Working name — "AI," "Human Experience," "Self" — explicitly undecided.

Time/Math/Architecture/Computer Science share a property: each is a formal, structural mode of orientation that needs no stance on culture, value, or subjective experience — a duration is the same duration regardless of who's asking, the same way `1 + 1 = 2` doesn't depend on who's doing the arithmetic. Human experience (fear, guilt, love, loyalty, meaning) is not obviously the same kind of thing — interpreted, value-laden, culturally situated, where two traditions can disagree about what an experience *means* in a way two mathematicians cannot disagree about `7 ÷ 2`. Treating "Human Experience" as a straightforward peer of the other four is not obviously right, and this doesn't assume it is — it may instead belong closer to Knowledge (material to reason *over*) or to the agent's own state, rather than beside Time and Math.

At least two distinct things are actually bundled under one proposed name: a **persistent self-model** (the agent's own continuous reference frame for distinguishing "I," "the user," "another person," "the world" — this is *state*, closer to `G` or a new component in the `A_t` tuple than to a callable Faculty), and a **candidate reasoning capability** over human/relational/normative situations (this *could* eventually be Faculty-shaped, but only if it meets the same reuse/genuine-independent-existence bar already applied to Time and Math — nothing here meets that bar today). Recommendation: keep these two threads separate going forward rather than one fifth faculty to be named — "AI" specifically is a weak candidate name for either, since it only restates what kind of system the agent is.

A narrow, concrete data point (2026-09-08): the ASK/SUGGEST interaction work in `docs/planning-model.md` needed the agent to have explicit access to its own immediately preceding contribution to correctly interpret a reply — addressed as a plain function parameter (`generate_plan()`'s `prior_suggestion`/`reply`), not any form of self-representation, but a concrete instance of the same underlying question: an agent that must correctly attribute "what I said" vs. "what the user said" needs *some* continuous reference to its own prior output, even at the smallest scale.

Genuinely new here: extracting a *structured* representation from a narrative source — entities (person, event, place, action) and the human-experience concepts attached to a person within it (fear, conflict, power, loyalty, betrayal, guilt, hope) — turning one concrete story into reusable, abstract relational/experiential material, without the agent "believing it is" that figure. A further proposal — giving a text's metaphysical/transcendent reference (e.g. "God") its own formal entity type — needs more caution than religious sources generally already get here: labeling *that* a text's God-reference is best modeled as one particular entity type is itself an interpretive choice, not a neutral structural fact, since different traditions hold materially different metaphysical stances about what such a reference even is.

The most speculative part, flagged as such: the idea that the agent could represent a relational or normative principle ("treat others as you would want to be treated") and apply it to a new situation, rather than hardcoding a rule. This is the one part of this entire document that most directly raises the stakes — quantitative and temporal reasoning are formal and checkable; normative/relational reasoning is exactly the kind of judgment where getting it wrong is both easy and consequential, and "the agent reasoned its way to this conclusion" is not on its own a justification for having reached it. Recorded as a question worth returning to, explicitly not a direction decided on, and any future work on it would need its own, much more careful pass.

**Placement:** none of this is a Domain, Faculty, class, knowledge graph, parser, moral-reasoning engine, or consciousness system, and none of it changes the existing Goal → Plan → Action → Feedback → Replan model. Whether a self-model belongs in a future `A_t` tuple, and whether a normative-reasoning capability ever earns Faculty status, are both left genuinely open.

## 4. Planning and product features

Speculation in this section keeps Goal/Plan wording; map those labels via [[04-current-state]] § Vocabulary when reading against today's code.

### i. Plan as an ordered step list

With "Task (right now)" as just the current step in it — instead of today's model, where `right_now` is its own independently-generated text field with no real connection to a "step 2" waiting after it. Discussed 2026-08-21, directly motivated by the drift bug fixed the same day ([[05-decisions]]): without a real step list, nothing *structurally* stopped `right_now` from drifting into something meaningless — fixing it needed a promise in the prompt ("only shrink once"), not something the data shape itself prevented. A real step list (step 3 of 7, inspectable) would make that kind of drift harder to produce in the first place.

- Decided so far: the whole list is generated in one go, not built incrementally step-by-step — but flagged as still needing its own conversation, because a full `one_year` step list could get very long.
- Explicitly deferred: which horizons actually become step-lists (`this_week` only, or `one_month`/`one_year` too) — "we take it bit by bit, but it's something to come back to."
- Concept for when feedback changes direction: start simple — it changes which step it's currently asking about (edits/swaps the current step), not a full regeneration of the whole list. Real, named, unsolved problem this runs into immediately: steps have implicit prerequisites ("you can't put water in the kettle before you've gotten off the couch") — freely editing one step in isolation can silently break the steps that assumed it. Explicitly parked, not solved, at the concept stage.
- Raised 2026-08-23: click into any individual step and generate steps FOR that step — the same "break this into smaller pieces" mechanism `_generate_steps()` already applies once to `right_now`, applied recursively/on-demand to any step in the list, drilling down as deep as needed. Same unsolved prerequisite problem as above applies one level deeper too (sub-steps inherit whatever their parent step assumed) — not a separate problem, the same one, just recursive.
  **Partly built 2026-09-14** — recursive zoom for the Steps *scratch* tree (later under `panes/canvas/call_suggest` / edit paths for Projects Suggest); real-plan persistence questions remain (see [[04-current-state]] § 5, § 9). The prerequisite problem above is still entirely unsolved: `Step.ordered` records *whether* a step's children have to happen in sequence, which is a flag, not knowledge of what any particular child assumed.

### ii. Recognize a real, already-happened start time

E.g. "I started yesterday" — pass it to the model as context, distinct from `duration` (how far the plan should span *forward*) and from `PLAN_KEYS` (the plan's own forward-looking horizons, year down to right_now) — neither currently captures "this didn't start from zero just now." Discussed 2026-08-21, while expanding `PLAN_KEYS` to `today`/`this_hour`/`this_minute`: a real, if uncommon, case — flagged as its own mechanism (recognition + context passed to the model), not an extra `PLAN_KEYS` entry, since it answers "when did this actually begin" rather than "how does the plan look at this time window." Likely the same deterministic-phrase approach as `backend/agent/specialized/outcome_classifier.py` (no LLM guessing on *whether* a start time was named) if/when this gets built.

### iii. Export/share a goal's plan as a document

Let the user send or print a goal's plan (and maybe its full conversation history) as an actual document/file, not just something viewed live in the devtools UI. Raised 2026-08-23, explicitly flagged by the user as "for later" while working on the horizon-scale diagram in `active/_timeperiod.html` — not scoped or designed at all yet (format, what's included, whether it's a real feature or just a personal debugging convenience — in the spirit of the static-snapshot tool that used to live at `backend/devtools/view.py`, removed 2026-08-24 once it turned out to be unused, see `backend/README.md`).

### iv. Fact-checking as a layer on the future Knowledge/RAG room

Plus a three-way split of knowledge types. Discussed 2026-08-24 (from a ChatGPT summary the user brought in) — not a new build, an addition to § Knowledge (in the settled-architecture document) once that room gets built:

- RAG and fact-checking are different things. RAG (retrieval) finds the stored chunks closest to a claim/question. Fact-checking is one function *built on top of* that retrieved material — it hands the claim and the sources to the model and asks for a verdict (e.g. "supported" / "mixed evidence" / "not supported" / "unknown") with the sources shown back to the user, instead of the model answering from training alone as if it knows for sure.
- Pairs with keeping three kinds of knowledge distinct rather than blended in a response: personal (the user's own notes, experience, history, stated preferences), external (papers, documentation, other verifiable sources), and system data (dates, goals, actions, actual stored history — what the system already knows for certain). Same shape as the principle already followed elsewhere in the project for time understanding, goal identity, and step counting: don't let the model guess or invent what deterministic code or a real source can already establish.
- Suggested build order once any of this becomes real: Goal → Plan → Feedback → History → Knowledge/RAG → Fact-checking. Fact-checking is meant to land as one function using the Knowledge layer, not a separate system built from scratch.

### v. Semantic understanding of time, not just numeric duration

Discussed 2026-08-24: the agent should understand what a duration actually means in context, not just convert it (1 hour = 60 minutes). One hour of reading is a lot; one hour of training is comparatively little. The same hour is also relative — long next to 15 minutes, short next to a full day. Consequence for planning: if the user only has 45 minutes available, the agent shouldn't automatically shrink whatever plan already exists — it may need to choose a different activity or plan entirely, not a shorter version of the current one. Overlaps with the "only shrink once" constraint noted in § 4.i above ([[05-decisions]]) and with the existing `duration`/`PLAN_KEYS` machinery (§ System structure, in the settled-architecture document). Directly what prompted the "Faculties" framing there, same day. Open design questions as of 2026-08-25:

- Where "what this duration means" comes from: RESOLVED for the relative-duration half — deterministic, hardcoded thresholds (`_RELATIVE_LENGTH_THRESHOLDS`), the "code decides, model is just told" principle ([[05-decisions]], 2026-08-20) applying here too. STILL OPEN for the activity-specific half: lookup table vs. model-informed reasoning, not decided.
- Whether this belongs to the Time faculty or a different one: RESOLVED for relative-duration (pure magnitude comparison needs no knowledge of activities, fits Time cleanly). STILL OPEN for the activity-specific half — looks like it belongs to a Language/Semantics faculty that doesn't exist yet.
- What "relative" duration requires: RESOLVED — a second duration string to compare against (`reference` in `relative_length(duration, reference)`). Nothing calls it with a real reference yet.
- The actual trigger: STILL OPEN — `relative_length()` exists as a capability, isn't wired into `plan.py`/`replan()`/the UI anywhere yet, so whether it runs on every plan generation or only on shrink is undecided.
- Noted 2026-09-14, not decided: the activity-specific half may be the same absent input as the depth verdict's own weak spot on the structural axis. `zoom.py`'s `is_too_coarse()` judges a step's wording without knowing whose step it is, exactly as `relative_length()` judges a span without knowing what it is a span *of* — and `planning-model.md` § Structural axis already states that resolution is "not a property of the text itself". If it is one gap rather than two, it is one thing to fix (see [[04-current-state]] § 9). Also a steer against the lookup-table option above: `planning-model.md` § Minimum planability counts "reliable general/background knowledge the agent already has access to" as KNOWN, and how long a run typically takes is exactly that — which makes this a model question, not a table to maintain.

### vi. The agent actually doing things, not just explaining how

Discussed 2026-08-24: distinguishes an agent that tells the user how to do something from one that produces the finished result itself. Concrete example raised: an app that generates Excel files, Word documents, text notes, or recipes, and uploads them to Google Drive. The specific file formats aren't the point — the point is going from a stated intention to an actual completed artifact. Flagged as close to the core definition of "agent" in this project (see [[00-project-brief]] — "Does the system make its own decisions?"). This is the output/action counterpart to § 5.ix below (aggregation / world-data), which is about the agent pulling information in.

### vii. Goal ≠ Plan: the goal stays stable, the plan is revisable

Discussed 2026-09-01, following a Goal-card UI and generation-logic review (see [[04-current-state]]): a Goal ("run a marathon", "get a visible six-pack in six months") represents what the user actually wants, and should not be redefined just because a plan built toward it stops working. A missed day, a missed week, or a plan that no longer fits reality is a signal that the *plan* has diverged from reality, not that the *goal* has failed or shrunk. The agent should re-evaluate and replan toward the same stated goal — never quietly substitute an easier goal the user never actually agreed to (e.g. two failed weeks of "run a marathon" is not license to redefine the goal as "run 10km").

- Sketch of the resulting flow, not decided or built: `GOAL → MILESTONES/DIRECTION → CURRENT PLAN → ACTIONS/STEPS → REALITY → USER FEEDBACK → AGENT EVALUATES → REPLAN → NEW CURRENT PLAN → CONTINUE TOWARD SAME GOAL`.
- For longer-horizon goals, milestones may be a third layer worth keeping distinct from both Goal and Plan: more stable than the current plan (revisable continuously without touching them), but not fixed like the goal itself — e.g. "establish a running routine" → "run 10km comfortably" → "run 20km" → "complete long training sessions" → "marathon-ready". The plan between milestones can change freely without the milestones changing.
- Consequence for today's implemented model (`Goal → Plan → Timeperiod → Action → Steps → Feedback` as six sequential UI sections, see [[04-current-state]]): these may not be six conceptually equal things. Sketched alternative grouping, not adopted: Vision → Goal (desired outcome, constraints/preferences, milestones/direction, and a current-state/plan sub-group holding relevant horizons, current action, and steps) → Feedback/reality → re-evaluation → new plan, continuing toward the same Goal.
- Explicitly not a decision to restructure the existing templates or data model this way — a conceptual principle to hold onto for when the generation logic itself becomes more agentic. Today's mechanical rules (`step_count()`'s fixed [3,6]/15-minute formula, `_HORIZON_LENGTH_THRESHOLDS`) are a temporary stand-in for judgment the model doesn't do yet, not a product principle to preserve.
- Overlaps § 4.i above — the prerequisite/replanning problem raised there (editing one step can break steps that assumed it) is a narrower version of this same replan-without-redefining-the-goal question.

### viii. Reflection / progress summaries

E.g. "you actually trained 1 hour/week — that's 52 hours this year."

### ix. Practices, not projects: a recurring commitment has no shape yet

Raised 2026-09-14, from two examples offered as interchangeable and structurally identical: "save 10 kroner every day" and "do 10 push-ups every day, and see how far it goes." Neither fits the implemented model on any axis. There is no deadline (explicitly open-ended — "see how far it goes"), so `duration`/`frozen_duration` have nothing to count down toward. There is no completion, so `resolved` never fires. And there is nothing to decompose — "do 10 push-ups" is already a single action, so the recursive Step of § 4.i is a tree with one node. What actually matters instead is a *rate* and an *accumulation*: how often, and what it has added up to.

Suggested name for the distinction, not a decided term: **projects** (climbing Everest, a master's degree, writing a song — a target, a depth, an end) versus **practices** (saving, push-ups, reading, tidying — a rhythm and a sum). Everything built today, including the on-demand zoom, addresses the project side.

- Why this matters more than its position in this document suggests: the motivating examples behind the project's own framing (include gaming, training, reading, cleaning in a day without any of it feeling like an obligation) are almost entirely practices, not one project among them. The shape the product cares most about is the one currently least represented.
- Open, and not investigated: whether a practice is a third kind of record alongside Goal and Vision, a Goal with a different set of fields, or something that isn't a Goal at all. Nothing here argues for one.
- Connects to § 4.viii above — accumulation ("52 hours this year") is the natural read of a practice, where for a project it is at best a side note.
- Second half of the same gap, also open: a practice that only knows what it is told can never notice that nothing has been logged for five days. For a practice, the *absence* of input is itself information, and nothing in the system acts between two user messages today (see [[04-current-state]] § 7, "Continuity / proactivity").

### x. A plan can only be regenerated, never edited

Raised 2026-09-14, from the wish to talk to a plan about one of its parts — "I finished step 2 already, on the 15th, not the 21st" — and the observation that this is close to what an issue tracker does, except with the agent doing the reorganizing rather than the user.

Three capabilities that this needs, separated deliberately because they are not the same thing and only the first is about objects: **reference** (the agent can tell which step is meant), **local mutation** (something changes at that step without the rest being rewritten), and **consequence** (the change propagates — six days freed up should move the windows of the steps after it). A recursive Step with a stable `id` (§ 4.i, built) supplies the first and nothing else.

- Concrete blocker found in existing code, not a design preference: `advance_step()`'s `step_status` is a per-step open/resolved list *parallel-indexed* to `steps`. Identity is therefore positional, and positional identity is incompatible with reorganizing — the moment steps move, the statuses silently describe different steps. Stable ids are what make reorganization expressible at all.
- Second blocker: `current_step` is one forward-only pointer per goal that advances "exactly once", so being done with step 2 but not step 1 cannot be represented. The implemented model assumes a ladder; both motivating examples ("we already did 1 and 2", "I completed step 2") assume something that isn't one. Whether every plan is a ladder is itself the question `Step.ordered` was added to hold an answer to.
- The deepest version of the gap: `replan()` regenerates a whole plan; nothing anywhere *edits* one. Keeping a tree and moving two nodes within it is a different operation from producing a new tree, and it does not exist in any form today.
- Tension to resolve rather than a bug: `frozen_duration` freezes a plan's windows deliberately, so a countdown doesn't silently reset on every render ([[04-current-state]] § 8). That is right for honesty and wrong for responsiveness. Possible reconciliation, untested — freeze the goal's *outer* span (a real deadline shouldn't drift) and recompute the steps' windows *within* it when something actually changes.
- Related but distinct from § 4.vii: that entry is about not redefining a Goal when a plan fails; this is about whether a plan can be changed in place at all.

### xi. Vision as what makes an activity legitimate, not a larger goal

Raised 2026-09-14, across two framings offered separately and probably the same idea: Vision as what determines which *framework* applies (a business vision implies metrics and deadlines; "get more healthy" implies consistency and has no deadline at all), and Vision as what makes an activity permissible rather than stolen time (gaming inside a vision of "a life I actually enjoy" is aligned, not a guilty pleasure).

Both point at Vision doing a **typing** job — deciding what counts as progress, what counts as success, and what vocabulary applies to everything underneath it — rather than being a bigger Goal above Goals. This would give Vision a concrete function, which is what it has been missing; it was paused precisely because it wasn't clear what it was *for*.

- Directly at odds with the implemented behavior, which is worth stating plainly: `judgment/prompts.py`'s Fill prompt (`SYSTEM_PROMPT` / `FILL_SYSTEM_PROMPT`) passes a linked Vision in as "background context only", instructed to "never let it override, replace, or expand what the goal itself actually asks for". That is the weakest possible use of it, close to the opposite of a typing mechanism. Not necessarily wrong — that instruction exists to stop the model inventing personal specifics from a vague direction — but the two readings cannot both be right, and nothing here decides which is.
- Why it may matter beyond Vision itself: the implemented vocabulary is uniformly one of obligation (`duration`, `frozen_duration`, deadlines, `resolved`, a forward-only pointer, a "Done?" control), while the product's stated aim is the absence of obligation. Two of the four motivating activities (gaming, reading) are things wanted and felt guilty about; two (training, tidying) are avoided but valued. They need opposite treatment and are currently treated identically, as goals with timeframes. Whether that dimension belongs to Vision, to a Goal, or somewhere else is open.
- Overlaps § 4.ix above — a Vision that implies "consistency, no deadline" is describing a practice, so these two may be one question approached from different sides.

## 5. Interface, platform, and delivery

### i. Multi-device sync via end-to-end encryption

Log in on a new device, get the same agent/history back; server never sees plaintext — see § Architectural principles (in the settled-architecture document).

### ii. Calendar integration

### iii. Push notifications / proactive outreach from the agent

### iv. iOS app with Swift/SwiftUI

### v. Android / cross-platform (React Native, Flutter)

### vi. Duolingo-style habit/identity mechanics (streaks, gamification)

### vii. Low-friction interaction

Voice, short text replies, one-button feedback, "agent only asks when necessary" (see [[00-project-brief]]).

### viii. Web interface translating portable data into a UI

Timeline, goals, progress views.

### ix. Aggregation / world-data capability

Weather, calendar, maps, resources, user's own past activity — a capability the agent can call on, not the core product. Let the free-text feedback note act as a real channel to the agent, not just status reporting: detect (deterministically, same approach as `backend/agent/specialized/outcome_classifier.py` — no LLM guessing on *what kind* of message it is) when a note reads as a question/request rather than a done/not-done/in-progress/goal-complete report, and route it through `replan()` as labeled feedback (e.g. "Asked: ...") so the agent actually responds instead of silently logging it as an unrecognized check-in. Found via real use, 2026-08-20: notes like "can you help me" / "maybe do some research for me" currently just get logged and ignored. Explicit caveat to carry into the eventual build: the agent still has no tools/internet access, so a "response" is bounded by the model's own training, not real live research.

### x. Minimal, stable visual identity for the agent

E.g. an abstract, non-human shape rather than a face or avatar, that the user encounters consistently across sessions — explored 2026-08-26 alongside relational continuity (§ 2.i above). The identity itself is not meant to carry personality or simulated emotion, only stable recognizability; any later states (idle/processing/speaking/noticing) should reflect real internal events, not simulated affect. Not scoped or designed — open question raised the same day: a face-like shape recruits face-perception more strongly than a fully abstract one (a light, a ring, a waveform), which may work against the "not a simulated person" intent.

### xi. "Notice" as a possible interface for a detected discrepancy

Instead of, or before, an explicit verbal statement from the agent, a subtle visual signal the user can choose to investigate. Explored 2026-08-26 alongside relational continuity (§ 2.i above); not designed. The same confidence/threshold/cooldown/"don't guess" discipline needed for any other intervention applies here — a signal fired on low-confidence data is exactly as costly to trust as a wrong verbal statement would be.

## 6. See also

- [[02-product]]
- [[05-decisions]]
- [[06-development]]
