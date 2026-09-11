# Collaboration

> **Migration note (2026-09-11):** copied here from `current/COLLABORATION.md` as the first step of migrating this project's docs/tools out of `current/` (see the parent conversation for the full plan). The `docs/00-06`, `tools/`, and `backend/`/`frontend/` references below still describe `current/`'s structure, not yet `v4/`'s — this note will be removed once each piece they reference has actually been migrated and the references updated to match.

How an AI coding session should work with this project — not what the project is (see `docs/00-project-brief.md`) or how code should look (see `CONVENTIONS.md`).

This is the project-specific instance of `global-standards/AI_COLLABORATION_GUIDE.md`'s general model: that guide describes how an AI session should establish and verify understanding of any software project; this file says concretely which documents and tools do that job here.

## Contents

- Docs
- Tools
- Before finishing
- Documentation tooling
- Meta-coherence

## Docs

Different questions about this project are answered by different documents, with different reliability — the same source-role model as `global-standards/AI_COLLABORATION_GUIDE.md` §2, mapped onto this project's actual `docs/` vault:

| Question | Start with | Role |
|---|---|---|
| What is the project trying to be? | `docs/00-project-brief.md` | Identity/vision — stable, rarely revisited |
| What's known from outside the project? | `docs/01-research.md` | External evidence — informs product/architecture, not settled itself |
| What is the product, concretely? | `docs/02-product.md` | Scope/intent — what's being built, not how |
| How is it meant to be structured? | `docs/03-architecture.md` | Intent, not proof of what's built |
| What is true now? | `docs/04-current-state.md` | Orientation only — verify against relevant code, structure, or runtime behavior when it matters |
| Why was it done this way? | `docs/05-decisions.md` | Settled, unless explicitly flagged |
| What happened, and when? | `docs/06-development.md` | Accurate for its date — not for today |
| What might happen? | `docs/06-development.md` § Parking Lot | Not decided, not built |

When judging the reliability of a specific piece of project information, keep fact, hypothesis, decision, and open question separate — see `global-standards/AI_COLLABORATION_GUIDE.md` §5 for the general model.

A well-argued idea in `docs/06-development.md` § Parking Lot, or anything marked open there, is not a decision — only `docs/05-decisions.md` holds settled ones, no matter how thorough the parked version reads.

If a decision in `docs/05-decisions.md` seems wrong, say why and flag it explicitly, rather than quietly working around it.

## Tools

Three scripts keep the mapping above honest — against itself and against the actual repository. Each owns a different concern; see each script's own docstring for exactly what it checks.

- **`tools/docs_check.py`** — structural integrity of `docs/`: expected files present, `[[wikilinks]]` and `docs/<name>.md` references resolve, each doc's own heading number matches its filename.
- **`tools/docs_lint.py`** — this project's documentation-neutrality style rule (`CONVENTIONS.md`), on `docs/` and code comments/docstrings.
- **`tools/project_check.py`** — broader repository orientation: wraps both of the above as sub-checks, plus git status, whether `docs/04-current-state.md` is older than the areas it describes, the actual `backend/`/`frontend/` trees, an import smoke test, pyflakes, and a few repo-hygiene checks nothing else covers.

At the start of a session, run:

    .venv/bin/python3 -m tools.project_check

then read `docs/04-current-state.md`. The output is what's mechanically observable right now, not proof the project is verified — each script only reports what it actually checks (see `global-standards/AI_COLLABORATION_GUIDE.md` §1).

Before renaming, moving, or deleting anything another file might reference, grep the vault and the code for the old name first; run `tools/project_check.py` afterward as the mechanical backstop, not a substitute for the grep.

Re-run `tools/project_check.py` before a consequential change, or once meaningful time or changes have passed since it last ran — it's cheap enough that this is rarely the wrong call.

## Before finishing

If your changes alter what's true about the project, update `docs/04-current-state.md` before ending the session (see `global-standards/AI_COLLABORATION_GUIDE.md` §9 for why a stale one is worse than none).

## Documentation tooling

> Moved from `docs/00-project-brief.md` § How We'll Document the Project, 2026-08-25 — this is operating practice, not project identity.

Several tools, different roles:

- **Paper** — thinking: brainstorming, sketches, questions, random ideas.
- **Obsidian** (`docs/`) — understanding and documenting. The project's permanent knowledge base.
- **Excel** — structuring and comparing (competitors, features, research, assessments, experiments); see `docs/01-research.md`'s comparison table for the in-vault version of the same thing.
- **GitHub** — building and documenting the software itself.

## Meta-coherence

A loose guideline, not a rule: documentation counts as real project information, not scratch, even though it isn't code — the reasoning behind a decision, or the shape of an idea before it's built, is still part of what the project actually is. The vault as a whole should read as one coherent, connected thing, not disconnected fragments.

Just naming how this vault already works:

- Cross-linked via `[[references]]` rather than left as isolated files
- Historical, dated entries preserved as accurate records of what was true when written, rather than rewritten once something changes (see `docs/05-decisions.md`)
- Code and docs reference each other in both directions — a docstring points to the doc that explains why, a doc points to the file that implements it
