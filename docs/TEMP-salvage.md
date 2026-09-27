# TEMP — Salvage from archived docs

> **TEMPORARY. This file exists only to be deleted.** It holds the few
> points from documents moved to `docs/archive/` that still matter for
> the current Map+Talk system, so the archive move loses nothing. Each
> item names where it belongs. When an item has been written into its
> home (or judged not needed), remove it here. When the file is empty,
> delete it and its entry in `tools/docs_check.py` (`EXPECTED_DOCS`).
>
> Created 2026-09-27 during the docs cleanup (`TODO.md` Active 42.3 /
> Queue 44.3). Not a source of truth — the archived originals are.

## Contents

1. For the rewritten `03-architecture.md`
3. For a UI document (`ui.md`, merged from `surfaces` + `visual-principles`)
4. For Talk demo polish (`TODO.md` Queue 46)
5. Checked and not carried over
6. Parked: NFT direction (from `02-product.md`)

(Section 2, for the project brief, was carried into the new
`00-project-brief.md` and removed.)

## 1. For the rewritten `03-architecture.md`

Source: `archive/v4-migration-decision.md` (Deterministic Program,
Architectural intent, The agent precisely, Boundaries). These outlast
the LLM1/2/3 design they were written for.

- **Division of labor.** "LLMs reason and interpret; deterministic
  software handles what requires determinism, state, persistence,
  validation, and concrete execution." Still how the code is built:
  storage, id minting, sibling numbering, saved trees, and slash
  commands are deterministic; only Talk replies, Suggest, and
  `/project_summary` call the model.
- **A role is not a model.** The job a model call does and the model
  behind it are separate; the model is swapped in one place
  (`backend/model/client.py`). Keep stating this.
- **"Agent" is not a component.** Agent = routing + capabilities +
  deterministic program + state + interface. No extra "agent
  intelligence" layer unless a demonstrated need justifies it.
- **The UI decides nothing** about a project or its tree and hosts no
  reasoning. It shows and sends.

## 3. For a UI document

Source: `archive/visual-reset.md` § Rule of the mirror, § How to work on
one area. Still true in the code today (`app/ui/src/panes/canvas/` ↔
`app/ui/css/panes/canvas/`, etc.).

- **Mirror rule:** `app/ui/src/<area>/…` ↔ `app/ui/css/<area>/…`, same
  area names on both sides. Behavior/DOM in `src/`, look in `css/`. A
  new visual surface gets or extends a pair — not a one-sided dump into
  `style.css`.
- **Tokens:** shared look lives once in `css/tokens.css`. If something
  should look the same everywhere, change a token; don't add a new hex
  value in an area file.
- **Shell is glue, not a parent:** sidebar, canvas, and chat are
  siblings; `shell/` holds layout, resize, and busy state.
- **Done-test for the look:** changing 2–3 tokens retints the whole UI;
  naming an area lets you open its `src/` and `css/` folders without
  hunting.

## 4. For Talk demo polish (`TODO.md` Queue 46)

Source: `06-development.md` § 4 Experiments (entries 5, 8, 9; tested on
`llama3.1:8b`, the model before today's `qwen3.5:9b`). About model
behavior, not the old engine, so they may still apply to Talk.

- **Invented specifics.** The model added plausible but ungrounded
  details the user never gave ("chapter 11", "a friend"). Risky
  precisely because it reads as reasonable.
- **Norwegian input.** Norwegian goal text produced answers unrelated
  to the goal, reproducibly (3 of 3), while the same goal in English
  was fine. The response then was to write in English. Worth re-testing
  on the current model, since the owner writes Norwegian.
- **Long chains drift.** When the model only saw the latest step, small
  changes compounded away from the goal; giving it the full history
  fixed it. Relevant to how much conversation Talk gets
  (`model/brief/conversation.py`, 20 turns).

## 5. Checked and not carried over

- `archive/goal-to-project-migration.md` — every phase done
  (2026-09-20). Leftover Goal naming is tracked in `TODO.md` 44.5; the
  out-of-scope list points at Queue items that already exist.
- `archive/v4-migration-decision.md` — LLM1/2/3 roles, Planning's
  ASK/SUGGEST/PLAN, data flow: the old design; decisions stay in
  `05-decisions.md`.
- `06-development.md` § 3 Development Log (closed 2026-08-26) and
  experiments about the old replan engine (1–4, 6, 7): history only.

## 6. Parked: NFT direction (from `02-product.md`)

Removed from `02-product.md` 2026-09-27 so the product text describes
only what exists. Not decided where it goes: back into 02 as a short
section, into `concepts.md` (not decided, not built), or the archive.
The API rule below ("all data through the API; the UI decides
nothing") is a current rule and belongs in the rewritten
`03-architecture.md` either way. Moved unchanged:

Stated 2026-09-25. A plan, not a decision — nothing here is built, and
none of it is to be built inside this application yet.

**The plan.** A separate application where a user creates an account,
gets a wallet with that account, and mints NFTs / tokens with it. This
application becomes an entrance to it, and the two are expected to
merge. A project created here would then be created on the blockchain,
not only locally.

**What it means for this application now.** All data enters through
the API (`app/backend/api/`); the UI only shows data and sends requests,
and decides nothing itself. Today's data is placeholder:

| Today (placeholder) | Later (from outside) |
|---|---|
| Accounts `account#N` (`data/accounts.json`) | Real accounts and wallets |
| `create_project()` mints a `project_id` locally | The project is created on-chain; the app receives its id |
| `backend/storage/` reads and writes local JSON files | The same place reads from / writes to the outside source |

The create pane (`backend/project/panes/create/` and `ui/src/panes/create/`:
projects, ids, and who owns which project) is the part that maps onto
accounts, minting, and ownership. `backend/storage/` is the only code that
touches data and `backend/api/` the only way in, so those are the two places that change when data
moves out; chat, map, and UI should not need to know where data lives.

Known gaps against this today (see [[04-current-state]]): the folder
picker opens a macOS dialog on the server; there is no written API reference; the server accepts
localhost only, with no login.

**Open questions (to settle before any chain work):**

- What goes on-chain and what does not. Every chain write typically
  costs a fee, and on-chain data is public and permanent; map and chat
  content is personal. One candidate split: ownership (this account
  owns this project, as a token) on-chain, content elsewhere and
  referenced from the token. Not decided.
- What an account is here, and how it relates to simulated users and
  to a "visit" (`TODO.md` Queue 27).
