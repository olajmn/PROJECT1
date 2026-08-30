# Collaboration

How an AI coding session should work with this project — not what the project is (see `docs/04-current-state.md`) or how code should look (see `CONVENTIONS.md`).

## Contents

- Before doing anything
- While working
- Before finishing
- Verifying claims about the project
  - Reliability of docs/ files
  - File paths and structure
  - Session statements and verification effort
- Documentation tooling
- Meta-coherence

## Before doing anything

1. Run `.venv/bin/python3 -m tools.project_check`, then read `docs/04-current-state.md`. The scan is what's actually observable right now (git status, what's changed since the doc was last touched, the real `backend/` tree, whether the core modules import, `docs_check`/`docs_lint` findings) — the doc is the fuller narrative. Treat the doc's claims as *believed*, not *verified*, until the scan confirms them or you check further yourself. Don't reconstruct the project's shape by guessing from memory or git history alone. A clean scan means the mechanical checks it ran found nothing wrong — not that the project as a whole is verified; it only covers what it actually checks.

## While working

2. Never invent facts about the project. If something isn't documented or isn't clear from the code, say so and ask — don't fill the gap with a plausible-sounding guess.
3. Keep four things separate, in what you read and what you write: **fact** (true now), **hypothesis** (untested belief), **decision** (settled, with a reason), **open question** (not yet resolved). Don't present a hypothesis as a fact, or reopen a decision without saying so explicitly. This is the session-level shorthand for the fuller taxonomy in `global-standards/DOCUMENTATION_STYLE_GUIDE.md` §5, used when writing into `docs/`.
4. A settled decision (`docs/05-decisions.md`) isn't revisited casually — if one seems wrong, say why and flag it, rather than quietly working around it.
5. Code and documentation style (language, tone, structure) is `global-standards/CODE_STYLE_GUIDE.md`, `DOCUMENTATION_STYLE_GUIDE.md`, and `CONVENTIONS.md`'s job, not this file's.

## Before finishing

6. If what you did changes what's true about the project, update `docs/04-current-state.md` before ending the session — a stale Current State is worse than none, since it's trusted by default.

## Verifying claims about the project

> Documentation and prior context — including this session's own earlier turns — are orientation, not proof. When a concrete claim about current code, structure, or functionality matters for a decision or a change, verify the relevant reality before building on it.

| Question | Start with | Role |
|---|---|---|
| What is true now? | `docs/04-current-state.md` | Orientation only — verify against relevant code, structure, or runtime behavior when it matters |
| How is it meant to be structured? | `docs/03-architecture.md` | Intent, not proof of what's built |
| Why was it done this way? | `docs/05-decisions.md` | Settled, unless explicitly flagged |
| What happened, and when? | `docs/06-development.md` | Accurate for its date — not for today |
| What might happen? | `docs/06-development.md` § Parking Lot | Not decided, not built |

### Reliability of docs/ files

7. `docs/04-current-state.md` is a claim, not a guarantee — accurate when last updated, not necessarily accurate now. Before acting on something it states about code/behavior, check the cheap way: `ls`/`find`/`grep`, read the file, run the thing.
8. A fact from `docs/06-development.md` carries its entry's date, not today's — that file exists to preserve old names/paths/reasoning accurately. Repeating a dated entry as present-tense fact is the file working as intended, misused. Cross-check `docs/04-current-state.md` or the code first.
9. Only `docs/05-decisions.md` holds settled decisions. A well-argued idea in § Parking Lot, or any "OPEN" question, is not a decision no matter how thorough it reads — state it as parked/open when repeated.

### File paths and structure

10. Never state a file path or structure from memory when it's about to be acted on. This project has been reorganized three times. `ls`/`find`/`grep` first, always — confidence is not evidence here.
11. Before renaming, moving, or deleting anything another file might reference, grep the vault and the code for the old name first. Every hit gets updated or deliberately left with a reason — never silently skipped. Run `tools/project_check.py` (it includes `tools/docs_check.py`) after, as the mechanical backstop, not a substitute for the grep.

### Session statements and verification effort

12. This session's own earlier statements are also orientation, not proof — re-check a claim against actual current state before acting on it, not against what was said many turns ago, even in this same conversation. Re-run `tools/project_check.py` rather than trusting an earlier scan once meaningful time or changes have passed since it ran.
13. Verification effort scales with what's riding on the claim — casual orientation doesn't need the rigor a claim that will drive an edit or get written into a doc as fact does. `tools/project_check.py` is cheap enough that "should I re-run it" is rarely the wrong question to ask before a consequential claim or change.

## Documentation tooling

> Moved from `docs/00-project-brief.md` § How We'll Document the Project, 2026-08-25 — this is operating practice, not project identity.

Several tools, different roles:

- **Paper** — thinking: brainstorming, sketches, questions, random ideas.
- **Obsidian** (`docs/`) — understanding and documenting. The project's permanent knowledge base.
- **Excel** — structuring and comparing (competitors, features, research, assessments, experiments); see `docs/01-research.md`'s comparison table for the in-vault version of the same thing.
- **GitHub** — building and documenting the software itself.

## Meta-coherence

A loose guideline, not a rule (2026-08-24): documentation counts as real project information, not scratch, even though it isn't code — the reasoning behind a decision, or the shape of an idea before it's built, is still part of what the project actually is. This doesn't mean every file needs a matching write-up somewhere — it means the vault as a whole, especially anything that could potentially become public, should read as one coherent, connected thing rather than disconnected fragments.

Nothing new to adopt — just naming how this vault already works:

- Cross-linked via `[[references]]` rather than left as isolated files
- Historical, dated entries preserved as accurate records of what was true when written, rather than rewritten once something later changes (see `docs/05-decisions.md`)
- Code and docs reference each other in both directions — a docstring points to the doc that explains why, a doc points to the file that implements it
