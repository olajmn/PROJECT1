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
backend/goal_to_plan.py
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

## See also

- [[09-mvp]]
- [[10-development]] — log of actual changes
- [[12-decisions]]
