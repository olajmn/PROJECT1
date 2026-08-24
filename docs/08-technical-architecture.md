# 08 — Technical Architecture

> Phase 6 in [[00-project-brief]]. See [[../CONVENTIONS.md]] for coding standards.

## Diagram

See `08-architecture.drawio` in this folder — a visual map of everything
the agent needs (green = built now, gray dashed = planned). Open it with
the free [diagrams.net](https://app.diagrams.net) app, or embed it
directly in this note with Obsidian's "Diagrams.net" community plugin.

## Current status (v0.1)

```
Terminal (input())
      ↓
backend/agent/specialized/plan.py
      ↓
Ollama (local server, localhost:11434)
      ↓
llama3.1:8b (local model, no API key)
      ↓
Plan printed to terminal
```

- Language: Python (code in English, see [[../CONVENTIONS.md]])
- Environment: `.venv/` (isolated per project)
- LLM: Ollama locally for now, can switch to Claude (`claude-opus-5`)
  later — both packages (`ollama`, `anthropic`) are installed

## Components the agent will need over time

- [x] LLM calls
- [x] Storage / database (plans, history) — `backend/storage.py`, JSON, unencrypted (see Security & Privacy Goals below)
- [ ] State (where the user currently is in the plan)
- [ ] Planning logic (beyond a single LLM call)
- [ ] Tools/APIs the agent can use
- [ ] Time/event system (proactivity, notifications)
- [ ] Temporal awareness — reasoning about time itself, not just text:
  current datetime, elapsed time, deadlines, "you set this goal 11 weeks
  ago", "you've postponed this task three times this week"
- [ ] Replanning logic
- [ ] Calendar integration (optional)
- [ ] Frontend (terminal → app), see the iOS discussion below

## Memory & Data Architecture (future, under consideration — not decided)

As history grows to years of data, the real problem isn't storage size —
it's how the agent efficiently finds and uses the *relevant* slice of
memory for a given moment. Not solved yet, and **not to be over-engineered
now**: JSON/local storage remains sufficient for the MVP.

One layout considered for later (illustrative, not a commitment):

```
project/
├── goals/
├── plans/
├── memory/
│   ├── 2026/
│   │   ├── 08-18.md
│   │   └── ...
│   └── 2027/
└── profile/
```

The point isn't that Markdown is the final format — it's that the data
stays portable and human-readable, consistent with the data-ownership
principle below.

**Refinement (2026-08-19):** the reason a folder-per-time-period layout
like this is attractive isn't just portability — it's that it makes a
future "scanning" planning algorithm close to free. If `one_year`,
`one_month`, `this_week` etc. are real folders/files on disk instead of
fields inside one flat JSON blob, an algorithm that needs to answer
"scan the 1-year plan, find how many weeks it covers, check status per
week" can just walk the directory tree instead of needing a database or
a custom index — the filesystem hierarchy *is* the index. This is the
concrete version of the still-unbuilt "Planning logic (beyond a single
LLM call)" and "Temporal awareness" items below. Still not decided or
built — `data/plans.json` remains sufficient while there's a handful of
records; revisit if/when Prototype 0.1 is validated and history grows
enough that "which week was this" becomes a real, felt problem.

## Data Ownership (long-term principle)

> The app should be able to disappear without the user's history
> disappearing.

If this project eventually becomes a kind of digital memory for the
user, the user shouldn't depend on the company or the app existing
forever. Inspired directly by Obsidian's approach to local Markdown
files. Long-term implications (not MVP work, tracked in
[[13-ideas-parking-lot]]):

- Local-first (see Multi-device vision below)
- Portable data, full export/import
- Cloud sync/backup as an *option*, never a requirement
- Encryption
- Access to the data without the app itself

## Security & Privacy Goals

**Explicit goal for this project:** locally stored data (goals, plans,
history) should eventually reach a level of protection comparable to a
password manager vault (e.g. Bitwarden) — i.e. encrypted at rest, not
just protected by OS file permissions.

Current status:

- [x] Whole-disk encryption via macOS **FileVault** (already on for this
  machine) — protects against the "stolen/lost laptop" scenario with
  zero project code
- [ ] Application-level encryption of `data/plans.json` itself (a
  master-password-derived key encrypting the file, `cryptography`
  package) — not built yet. Deferred: adds real work only in the form of
  UX friction (password prompt every run) and an unrecoverable-password
  risk, for protection against a narrower threat (a malicious process
  running as the logged-in user). Revisit before this becomes a
  multi-user or cloud product — see [[12-decisions]].
- [ ] Encryption in transit — not relevant while Ollama is local-only
  (`localhost`, never leaves the machine); becomes relevant again if/when
  Claude API or any cloud sync is added (HTTPS handles this by default).

### Multi-device vision (later): local-first, not blockchain

**Goal (two parts, both explicit user requirements):**

1. Log in on a new device with just a password/key and get the full
   "agent" back (history, context) — without trusting the server
   operator to be able to *read* the data.
2. No single company should be able to *lock the user out of* or
   *control access to* their own data (decentralization of control, not
   just of confidentiality).

**Part 1 → end-to-end encryption**, the same pattern Bitwarden/1Password/
Signal use. Key derived locally from password → data encrypted locally →
only the encrypted blob is ever uploaded → any device with the same
password derives the same key and decrypts locally. The server never
sees plaintext ("zero-knowledge").

**Part 2 → local-first architecture**, not blockchain. Blockchain solves
consensus among mutually-distrusting *strangers* via a public ledger —
the wrong tool here both because "public" is the opposite of private,
and because our problem is ownership/lock-out, not consensus. The
established answer for "no company can lock me out" is the **local-first**
principle ("Local-first software: you own your data, in spite of the
cloud" — Ink & Switch):

- The user's own device always holds a complete copy of their data — a
  sync server going away loses nothing
- Data stays in an open, ordinary format (JSON — already true today) so
  it's never locked into one vendor's proprietary storage
- Any future sync server is a **replaceable relay**, never the owner of
  the truth — if it disappears, sync can point elsewhere (a different
  server, self-hosted, peer-to-peer) without the app breaking
- Combined with the encryption from Part 1, even the relay operator
  can't read the data, only store/forward it

**Note:** the project is already 100% local-first today, by construction
— there is no server at all yet, only a local file. The design goal going
forward is to *preserve* this property when sync is added, not to
introduce a dependency on any one company's server.

Requires a real backend + account system to build, so this is explicitly
**not** an MVP concern — see [[13-ideas-parking-lot]].

## Frontend direction (iOS)

The backend (agent logic, LLM calls, database) and the frontend (the app
on the phone) are two separate choices — they don't need to be the same
language.

- **Backend:** can stay in Python (strong LLM/AI ecosystem), runs as a
  server the app talks to over an API.
- **iOS app:** Swift + SwiftUI is Apple's modern, recommended native
  stack — best for deep OS integration (push notifications, widgets,
  background tasks), which matters for a "proactive" agent. Alternative:
  React Native/Flutter if Android also needs to be supported from the
  same codebase, at the cost of some native depth.
- This isn't a decision the MVP needs right now — see [[09-mvp]].

## Long-term architecture (vision, not current — do not build yet)

Aggregation (weather, calendar, maps, resources, the user's own past
activity) is **not** the core product — it's a capability the agent can
call on when reasoning about the next action. The agent is the core
product. Full long-term shape, for orientation only:

```
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

A future **web interface** would sit on top of the same portable data
(see Data Ownership above) and translate it into UI — not just a control
panel, but timelines/visualizations of the user's own history:

```
Markdown / JSON / structured data
             ↓
          Web UI
             ↓
     ┌───────┼────────┐
     ↓       ↓        ↓
 Timeline   Goals   Progress
```

None of this is being built now — see [[13-ideas-parking-lot]] and the
testing philosophy in [[09-mvp]].

## Faculties: a third axis, alongside Rooms and the pipeline (2026-08-24)

> **Terminology update, later the same day:** this section originally
> used two separate words - "Room" (one product concept, narrow) and
> "Faculty" (a shared capability, broad) - as two different categories.
> Simplified: **"Faculty" is now the one word for a module in this
> project**, full stop - "module" is the plain, standard programming
> term for it; Faculty is just this project's own name for that, the
> same way other projects have their own house term for the same
> concept. What used to be the Room/Faculty split is now described as
> **narrow** (used by exactly one thing, e.g. the Goal faculty) vs.
> **broad** (reused across more than one, e.g. the Time faculty) - a
> property of a faculty, not a separate category name. `specialized/`
> and `distributed/` remain the actual folder names, unchanged - only
> the words used to talk about them changed. Everywhere below that
> still says "Room" is the historical record of how this thinking
> developed over the day, kept as-is rather than rewritten - read
> "Room" as "narrow faculty" and the reasoning still holds.

Raised 2026-08-24, prompted by two things that happened the same day:
`backend/timeperiod.py` outgrew one file and was split into a package
(`matchers.py`/`resolve.py`/`frozen.py`), and the "semantic
understanding of time" idea was logged in [[13-ideas-parking-lot]].
Both pointed at the same underlying question - not "what does the
product do" (Rooms, [[07-features]]) and not "what happens, in what
order" (the pipeline diagram above), but "what does the agent
understand or know how to do, independent of which Room or pipeline
stage is asking." Went from framework to actually built the same day
- see "Built the same day" below.

**The three axes, made explicit:**

| Axis | Answers | Example |
|---|---|---|
| Rooms ([[07-features]]) | What does the product do? | Goals, Plans, Conversation, Knowledge |
| Pipeline (diagram above) | What happens, in what order? | User -> Reasoning -> Planning -> Action -> Result |
| Faculties (this section) | What does the agent understand, regardless of when/where it's needed? | Time, Language, Semantics |

**This isn't a novel idea - it has established names.** Three
independent traditions land on the same Rooms/Faculties split, which is
a sign the split tracks something real rather than personal taste:

- **Domain-Driven Design** (Eric Evans, 2003): Rooms = *Bounded
  Context* (a self-contained part of the system with its own model);
  Faculties = *Shared Kernel* (logic more than one bounded context
  needs, that belongs to none of them alone).
- **"Package by feature" vs. "package by layer"** - a long-running
  organize-by-domain-concept vs. organize-by-technical-role debate.
  Rooms is package-by-feature; a faculty is the piece that doesn't fit
  under any one feature's package no matter which side wins.
- **Monorepo convention**: `apps/` (Rooms - product-facing) vs. `libs/`
  or `shared/` (Faculties - reused capabilities), the layout tools like
  Nx/Turborepo default to once a codebase outgrows a single package.
- **Cognitive architecture** (Soar, ACT-R): the closer analogy than
  "left brain / right brain" (a popular but scientifically unsupported
  framing - both hemispheres are involved in nearly everything) is
  *specialized brain regions* (vision, motor control - one clear job
  each, like Rooms) vs. *domain-general faculties* (attention, working
  memory - not localized to one region, drawn on by all of them at
  once, like Time here). These frameworks name working
  memory/procedural memory as exactly this kind of shared,
  non-task-specific system.

A faculty is a cross-cutting concern - something more than one Room and
more than one pipeline stage all lean on, rather than something that
belongs to exactly one of them. Time understanding is the clearest
existing example: it's used when a goal's text is first parsed ("this
weekend" - the User stage), when the plan is divided into steps (the
Planning stage), and when the UI draws a countdown (display) - not
owned by any single Room or pipeline stage, borrowed by all of them.
"Entity, not robot" captures why this matters: a
handful of real, reused faculties is what makes the difference between
a coherent agent and a pile of disconnected scripts that happen to
share a repo.

**Built the same day, once the user decided the physical split was
worth having for its own sake** - not for the code as it stood, but
for clarity about what to build next (a legitimate, different reason
than "the current code needs this"; the two can point different ways,
and did here). `backend/` now has:

```
backend/
  storage.py            <- neither Room nor Faculty - persistence
                            infrastructure, so it stays at this root
                            level rather than forcing a third category
  specialized/           <- narrow faculties: goal.py, plan.py, today.py,
                            outcome_classifier.py, outcome_phrases.py
  distributed/            <- broad faculties: timeperiod/, timesegments.py
  devtools/              <- unchanged, its own separate concern
```

Two decisions worth recording, because the reasoning generalizes to
every future faculty/Room call:

- **`storage.py`'s category question was revisited later the same
  day** (see "Infrastructure: a fourth category" below) - it does NOT
  simply stay uncategorized at `backend/`'s root by default; that
  placement turned out to have a real reason once someone actually
  asked what storage.py *does*, not just where it's convenient to
  leave it.
- **Sharing an implementation *pattern* isn't the same as sharing a
  *faculty*.** `outcome_classifier.py` (specialized/) recognizes
  feedback phrases the same deterministic way `timeperiod/matchers.py`
  (distributed/) recognizes time phrases - both follow this project's
  "code decides, model is just told" principle (see [[12-decisions]],
  2026-08-20). That shared technique was raised as a real reason to
  treat them as one faculty. Resolved by going back to the faculty
  test already defined above - reused across more than one Room, not
  "built the same way": `outcome_classifier.py` is used only by Goal's
  own feedback flow today, so it stays in `specialized/`. If it's ever
  genuinely reused by another Room, that reuse is the signal to
  reconsider, exactly as it was for Time.

### Infrastructure: a fourth category (2026-08-24)

`storage.py` was left at `backend/`'s root level, un-categorized, when
`agent/`/`world/` were first built - flagged as an open question, not
answered. Answered the same day by applying the Faculty test honestly
instead of by default: `storage.py` (`save_plan()`, `load_history()`,
`get_latest_plan()`) is imported by every single Room
(`goal.py`/`plan.py`/`today.py`) AND by `devtools/app.py` directly -
more reuse than Time ever had. By the reuse test alone, it looks like
the most obvious Faculty in the whole project.

But a Faculty was defined above as something the agent *understands*
- and `storage.py` understands nothing. It doesn't interpret what it
saves, the way Time interprets "evening" or Recognition interprets a
feedback phrase (see below) - it just moves bytes to and from a file.
Passes the reuse test, fails the actual definition.

That's not a flaw in the model - it's evidence a category was missing.
**Infrastructure**: shared technical machinery, reused broadly like a
Faculty, but understanding nothing, unlike one. `storage.py` stays
exactly where it physically is (`backend/storage.py`, sibling to
`agent/` and `world/`) - not because the question is still open, but
because Infrastructure is a real, separate, resolved answer, not a
default for "didn't fit the other two."

The body analogy that landed this: not an eye (Perception - senses the
outside world) but a hippocampus, or plainer, a hand writing in a
diary - the *mechanism* of remembering, understanding nothing about
what's actually written.

### Cognition and Recognition: a sharper name for the data/logic pair (2026-08-24)

A courtroom analogy, and a better name than "data vs.
logic" for a pairing pattern this project already followed twice
before naming it: **Cognition** is the fixed rules themselves - the
"law," written once by a developer, that doesn't change while the
program runs (`timesegments.py`'s `DAY_SEGMENTS`/`PERIOD_PHRASES`,
`outcome_phrases.py`'s `GOAL_DONE_PHRASES`/`RULES`). **Recognition** is
the "judge" - the matching logic that takes a real, specific input and
decides what in the law it satisfies (`timeperiod/matchers.py`,
`outcome_classifier.py`). Cognition doesn't do anything by itself;
Recognition doesn't know anything by itself - each pairing needs both.

**Acting** is the third piece of the same courtroom picture - not the
law, not the judge, but the "bailiff" who actually carries out the
ruling. This is exactly the still-unbuilt "agent actually doing
things, not just explaining how" idea in [[13-ideas-parking-lot]] (the
same 2026-08-24 entry already linked above): today, `resolve_duration()`
and `classify_outcome()` (Recognition) both stop at a verdict - they
never *act* on it. Naming this "Acting" doesn't move it out of the
parking lot, it just gives the eventual faculty a name once it's real.

**Not a new folder split.** Cognition/Recognition/Acting describes a
pairing *inside* both `specialized/` and `distributed/` (each already
has a Cognition file next to its Recognition file) - it doesn't
compete with the Room/Faculty axis or the User/World/Memory axis
above, it's a third, orthogonal lens on the same code, same as the
data/logic language it replaces.

**A deeper version of the same idea, from Norwegian law** (raised the
same day, kept here only for the one useful mapping, not the full
legal system): Cognition/Recognition already match "Lov" (the fixed
rule) and "Vedtak" (the ruling that applies it) reasonably well. One
extra rung is worth naming because it already exists, just not under
this label: **CONVENTIONS.md and [[12-decisions]]** are this project's
own "Grunnlov" - the highest-level, rarely-changed principles ("code
decides, model is just told") that every Cognition file's rules are
themselves answerable to. "Forskrifter" (a rung between law and
ruling) has no equivalent in the code today - not built, not needed
yet, noted here only so it isn't reinvented from scratch if a real
in-between layer ever shows up.

**Not decided yet, deliberately:**
- The full list of faculties - Time is the only one with real code
  behind it today; `distributed/` has exactly one resident. Candidates
  identified but NOT settled: Language, Semantics,
  Memory/Knowledge (overlaps the Knowledge room above - relationship
  not resolved), Action/Doing (overlaps the ACTION node in the
  pipeline diagram above - relationship not resolved; see
  [[13-ideas-parking-lot]]'s "agent actually doing things" entry, same
  day). Rough estimate: around 5 total.
- Whether Semantics and Language end up being the same faculty or two.
- How a faculty differs from a Room in cases where they clearly
  overlap (Knowledge, Action) - whether one contains the other, or
  they're just adjacent framings of related-but-different questions.

**When to add a second resident to `distributed/`:** the same
evidence bar as `outcome_classifier.py` above - real reuse by more
than one Room, not just a plausible-sounding name. Until then,
`specialized/` carries everything else, undifferentiated, the same
way `backend/`'s flat layout did before this split.

### The full picture: agent/ and world/, one of them still empty (2026-08-24)

Prompted by a longer cognitive-architecture breakdown the user brought
in from a ChatGPT conversation the same day (Perception / Memory /
Self / Goals / Reasoning / Emotion / Executive control / Temporal
awareness - a framing close to BDI agent architecture from AI research,
crossed with executive-function psychology). Two pieces of it are
genuinely new to this project - **Self/Identity** and
**Emotion/Affect** - the rest already had names here, just different
ones (Memory -> History/Knowledge, Temporal awareness -> the Time
faculty, Reasoning -> Plan, Control -> steps/current_step).

The useful result wasn't adopting all eight boxes - it was locating
`specialized/`/`distributed/` as one small piece of a bigger, mostly
*unbuilt* picture, and answering a real question along the way: where
does "external info" (weather, calendar, web search, documents) fit,
versus the agent's own accumulated memory of one user? The long-term
diagram above already answers this - it has MEMORY, WORLD,
and USER as three *separate* nodes, not two. World = live external
data sources. User = the channel a human actually talks to the agent
through. Easy to conflate (both are "outside memory"), but they're not
the same thing.

**Naming footnote:** "memory" was considered and rejected as the name
for the wrapper folder - the initial instinct was to use it broadly
(phylogenetic/instinctual "memory," DNA-coded, as a metaphor for
hardcoded cognition generally - a real, named distinction in biology:
phylogenetic vs. ontogenetic memory), but this doc had already claimed
"Memory" narrowly (History/Knowledge specifically), so the same word
meaning two different things at two different scopes would have
collided the first time someone read `agent/goal.py` and wondered why
goal logic lives under "memory." `agent/` was picked instead -
zero collision, and it's the word this project already uses for the
whole system everywhere else.

**Built 2026-08-24** (moved by the user directly, verified/repaired
afterward - imports, run commands, and every doc reference updated to
match):

```
backend/
  agent/                     <- the agent's own cognition - BUILT
    specialized/                Rooms
    distributed/                 Faculties (Time only so far)
  world/                     <- external data - BUILT AS AN EMPTY
                                 PLACEHOLDER ONLY. Zero code behind it
                                 (nothing external is fetched anywhere
                                 in this project today, by design - see
                                 [[13-ideas-parking-lot]]'s "no tools/
                                 internet access" caveat). Its
                                 __init__.py explains why it exists
                                 despite being empty - also the only
                                 reason git tracks it at all, since an
                                 empty directory isn't a real git entry
                                 on its own.
  storage.py                 <- OPEN QUESTION, not resolved: should
                                 this move inside agent/ too (it's the
                                 agent's own persisted memory, arguably
                                 part of its cognition, not external)?
                                 Left at this root level for now because
                                 that's where it already was, not
                                 because the question was settled.

devtools/                   <- the USER node - moved here 2026-08-24
                                (was backend/devtools/) - talks TO the
                                agent, isn't part of its cognition, see
                                devtools/README.md
tools/                      <- standalone dev utilities, no runtime
                                relationship to the agent at all
docs/                       <- documentation, no code
```

Unlike every other folder decision on this page, `world/` was built
empty deliberately, as a scaffold for future direction rather than
because real code exists yet - a deliberate exception, not a
violation of the "earn it" principle followed everywhere else on this
page, an explicit exception to it.

## See also

- [[09-mvp]]
- [[10-development]] — log of actual changes
- [[12-decisions]]
