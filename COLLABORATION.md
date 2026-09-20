# Collaboration

How an AI coding session should work with this project — not what the project is (see `docs/00-project-brief.md`) or how code should look (see `CONVENTIONS.md`).

This is the project-specific instance of `global-standards/AI_COLLABORATION_GUIDE.md`'s general model: that guide describes how an AI session should establish and verify understanding of any software project; this file says concretely which documents and tools do that job here.

## Contents

- Docs
- Tools
- Before finishing
- New code placement
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
| What might happen? | `docs/concepts.md` | Not decided, not built (moved here from `docs/06-development.md` § Parking Lot 2026-09-11 — see that document's own note) |

When judging the reliability of a specific piece of project information, keep fact, hypothesis, decision, and open question separate — see `global-standards/AI_COLLABORATION_GUIDE.md` §5 for the general model.

A well-argued idea in `docs/concepts.md`, or anything marked open there, is not a decision — only `docs/05-decisions.md` holds settled ones, no matter how thorough the speculative version reads.

If a decision in `docs/05-decisions.md` seems wrong, say why and flag it explicitly, rather than quietly working around it.

## Tools

Three scripts keep the mapping above honest — against itself and against the actual repository. Each owns a different concern; see each script's own docstring for exactly what it checks.

- **`tools/docs_check.py`** — structural integrity of `docs/`: expected files present, `[[wikilinks]]` and `docs/<name>.md` references resolve, each doc's own heading number matches its filename.
- **`tools/docs_lint.py`** — this project's documentation-neutrality style rule (`CONVENTIONS.md`), on `docs/` and code comments/docstrings.
- **`tools/project_check.py`** — broader repository orientation: wraps both of the above as sub-checks, plus git status, whether `docs/04-current-state.md` is older than the areas it describes, `app/`'s actual `backend/` tree, an import smoke test, pyflakes, and a few repo-hygiene checks nothing else covers.

At the start of a session, run (from the project root, against `app/`'s own venv - the only project this script's code checks target):

    app/.venv/bin/python3 -m tools.project_check

then read `docs/04-current-state.md`. The output is what's mechanically observable right now, not proof the project is verified — each script only reports what it actually checks (see `global-standards/AI_COLLABORATION_GUIDE.md` §1).

`/full-check` (`.claude/commands/full-check.md`) runs `project_check.py` plus `app/`'s full test suite (`test_math`, `test_time`, `test_data_persistence`, `test_feedback_parser`, `test_planner`) in one go, and reports a compact summary rather than raw output — the version of the above actually meant to be typed day to day.

Before renaming, moving, or deleting anything another file might reference, grep the vault and the code for the old name first; run `tools/project_check.py` afterward as the mechanical backstop, not a substitute for the grep.

Re-run `tools/project_check.py` before a consequential change, or once meaningful time or changes have passed since it last ran — it's cheap enough that this is rarely the wrong call.

## Before finishing

If your changes alter what's true about the project, update
`docs/04-current-state.md` before ending the session (see
`global-standards/AI_COLLABORATION_GUIDE.md` §9 for why a stale one is
worse than none).

If the session added or leaned on a **second path** beside an old one
(UI home, planner SoT, progression vs calendar, etc.), also update
root `TODO.md` § Parallel paths — dual code is fine; unnamed dual
code is how the base turns into a mess. See that section's anti-mess
rule and [[05-decisions]] #25.

## New code placement

When implementing something new in a session, **prefer** a new file
(or small folder) for a real new capability, then wire it with a thin
import — see `CONVENTIONS.md` § New code placement. Prefer, don’t force:
same-concern fixes and small extensions stay put; don’t invent micro-files
for ceremony or park a large new feature in an unrelated open module.

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
