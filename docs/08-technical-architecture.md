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

## Faculties: what "module" means in this project's folders (2026-08-24, trimmed 2026-08-25)

> **Faculty** is the word this project uses for a module - "what does
> the agent understand or know how to do, independent of which Room or
> pipeline stage is asking," in contrast with **Room** ([[07-features]])
> - "what does the product do." **narrow** (used by exactly one Room,
> e.g. the Goal faculty) vs. **broad** (reused across more than one,
> e.g. the Time faculty) is a property of a faculty, not a separate
> category. `specialized/` holds narrow faculties, `distributed/` holds
> broad ones - those are the actual folder names.
>
> **Trimmed 2026-08-25:** this section originally carried more
> vocabulary alongside the folder decisions - Cognition/Recognition/
> Acting naming, a courtroom analogy, a Norwegian-law analogy, and a
> cross-discipline validation against Domain-Driven Design, monorepo
> conventions, and cognitive-architecture research. Cut once it became
> clear the actual, recurring question was just "which folder does this
> code go in" - the rest was vocabulary-building beyond what that
> question needed. Full version recoverable from git history if ever
> wanted back.

Raised 2026-08-24, prompted by two things that happened the same day:
`backend/timeperiod.py` outgrew one file and was split into a package
(`matchers.py`/`resolve.py`/`frozen.py`), and the "semantic
understanding of time" idea was logged in [[13-ideas-parking-lot]].
Both pointed at the same underlying question - not "what does the
product do" (Rooms) and not "what happens, in what order" (the
pipeline diagram above), but "what does the agent understand or know
how to do, independent of which Room or pipeline stage is asking."

**The three axes, made explicit:**

| Axis | Answers | Example |
|---|---|---|
| Rooms ([[07-features]]) | What does the product do? | Goals, Plans, Conversation, Knowledge |
| Pipeline (diagram above) | What happens, in what order? | User -> Reasoning -> Planning -> Action -> Result |
| Faculties (this section) | What does the agent understand, regardless of when/where it's needed? | Time, Language, Semantics |

A faculty is a cross-cutting concern - something more than one Room and
more than one pipeline stage all lean on, rather than something that
belongs to exactly one of them. Time understanding is the clearest
existing example: it's used when a goal's text is first parsed ("this
weekend" - the User stage), when the plan is divided into steps (the
Planning stage), and when the UI draws a countdown (display) - not
owned by any single Room or pipeline stage, borrowed by all of them.

**Built 2026-08-24**, moved by the user directly, verified/repaired
afterward (imports, run commands, every doc reference updated to
match):

```
backend/
  storage.py             <- see "Infrastructure" below - reused
                             everywhere but understands nothing, so it
                             isn't a faculty either. OPEN QUESTION, not
                             resolved: should this move inside agent/
                             too (it's the agent's own persisted
                             memory, arguably part of its cognition,
                             not external)? Left here for now because
                             that's where it already was, not because
                             the question is settled.
  agent/                  <- the agent's own cognition
    specialized/             narrow faculties: goal.py, plan.py,
                              today.py, outcome_classifier.py,
                              outcome_phrases.py
    distributed/              broad faculties: temporal/,
                              time_segments.py (Time is the only one
                              with real code behind it so far)
  world/                  <- external data - BUILT AS AN EMPTY
                             PLACEHOLDER ONLY. Zero code behind it
                             (nothing external is fetched anywhere in
                             this project today, by design - see
                             [[13-ideas-parking-lot]]'s "no tools/
                             internet access" caveat), a deliberate
                             exception to the "earn it" principle
                             followed everywhere else on this page.
  devtools/                <- the USER node - talks TO the agent,
                             isn't part of its cognition, see
                             devtools/README.md
tools/                   <- standalone dev utilities, no runtime
                             relationship to the agent at all
docs/                    <- documentation, no code
```

**The reuse test, and why it matters:** `outcome_classifier.py`
(specialized/) recognizes feedback phrases the same deterministic way
`temporal/phrase_matching.py` (distributed/) recognizes time phrases - both
follow this project's "code decides, model is just told" principle
(see [[12-decisions]], 2026-08-20). Sharing that implementation
*pattern* was raised as a reason to treat them as one faculty -
rejected: `outcome_classifier.py` is used only by Goal's own feedback
flow today, so it stays in `specialized/`. **Real reuse by more than
one Room, not a plausible-sounding name, is what earns a spot in
`distributed/`** - the same bar `storage.py` gets held to next.

**Infrastructure - a fourth category, not a faculty:** `storage.py`
(`save_plan()`, `load_history()`, `get_latest_plan()`) is imported by
every Room AND by `devtools/app.py` directly - more reuse than Time
ever had. By the reuse test alone it looks like the most obvious
faculty in the project. But a faculty is something the agent
*understands*, and `storage.py` understands nothing - it doesn't
interpret what it saves, it just moves bytes to and from a file.
Passes the reuse test, fails the actual definition. **Infrastructure**:
shared technical machinery, reused broadly like a faculty, but
understanding nothing, unlike one. `storage.py` stays exactly where it
physically is - not because the category question is unresolved, but
because Infrastructure is a real, separate, resolved answer.

**Why `world/` is separate from `agent/`, not folded into it:**
MEMORY (the agent's own accumulated history of one user) and WORLD
(live external sources - weather, calendar, web search, documents) are
both "outside the agent's immediate reasoning," easy to conflate, but
not the same thing - the long-term diagram above already keeps MEMORY,
WORLD, and USER as three separate nodes. ("memory" was considered and
rejected as the wrapper folder's name for this reason - it would have
collided with "Memory" already meaning History/Knowledge elsewhere in
this doc; `agent/` was picked instead.)

**Not decided yet, deliberately:**
- The full list of faculties - Time is the only one with real code
  behind it today (including a first duration-relativity piece,
  `relative_time.py` - see [[14-semantic-time]], 2026-08-25); `distributed/`
  has exactly one resident still. Candidates identified but NOT
  settled: Language, Semantics, Memory/Knowledge (overlaps the
  Knowledge room above - relationship not resolved), Action/Doing
  (overlaps the ACTION node in the pipeline diagram above -
  relationship not resolved; see [[13-ideas-parking-lot]]'s "agent
  actually doing things" entry). Rough estimate: around 5 total.
- Whether Semantics and Language end up being the same faculty or two.
- How a faculty differs from a Room in cases where they clearly
  overlap (Knowledge, Action) - whether one contains the other, or
  they're just adjacent framings of related-but-different questions.

**When to add a second resident to `distributed/`:** the same
evidence bar as `outcome_classifier.py` above - real reuse by more
than one Room, not just a plausible-sounding name. Until then,
`specialized/` carries everything else, undifferentiated, the same
way `backend/`'s flat layout did before this split.

## See also

- [[09-mvp]]
- [[10-development]] — log of actual changes
- [[12-decisions]]
