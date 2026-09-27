# Project Conventions

Technical standards for this codebase. Applies going forward.

## Contents

- Language
- Interface style
- Documentation neutrality
- Code documentation
- New code placement
- Project structure
- Environment
- Security & privacy
- LLM backend

## Language

- English also applies to code, not just `docs/` (see `global-standards/DOCUMENTATION_STYLE_GUIDE.md` §1): variable/function names, comments, docstrings, log/print strings, and prompts embedded in code must all be in English.
- Live conversation with the assistant while working on the project can still happen in Norwegian — this rule covers files that get committed, not the chat itself.

## Interface style

- No emojis anywhere in the UI (button labels, status text, headings) or in generated content. Plain text only.

## Documentation neutrality

- Code comments, docstrings, and `docs/` files state the reasoning or consequence itself, not the personal narrative of how/when/by whom it was noticed — "X breaks without Y", not the story of the screenshot that revealed it; "the goal was X", not X framed as something personally wanted. Dated entries where the date is the point (the "Date:" field in `docs/05-decisions.md`) keep their dates; only the voice around them stays neutral.
- "The user" as a term still refers to the *product's* end-user where that's the actual subject (e.g. "the data stays on the user's machine") — this rule is about not narrating this project's own build process as a personal story, not about avoiding the word.
- The exact, checkable patterns this rule means are defined once, in `tools/docs_lint.py` (`_CONFIRMED_PATTERNS`/`REVIEW_PATTERN`) — not restated here. Run it (`python3 tools/docs_lint.py`, from the project root — stdlib only, no `.venv/` needed) rather than checking by eye; update the patterns there, not this paragraph, when a new case turns up.

## Code documentation

Source-code Contents (what a file's navigation block should contain, and when one is warranted) is defined in `global-standards/CODE_STYLE_GUIDE.md` §1-§2, not restated here. Document-oriented Contents is `global-standards/DOCUMENTATION_STYLE_GUIDE.md`'s job; `global-standards/_CONTENT_HIERARCHY.md` covers heading-hierarchy notation where that level of detail is needed. This project has no Contents rule of its own beyond those.

## New code placement

**Prefer** giving a **new capability** (feature, helper, pane behavior, policy with its own surface) its **own file** — or a small folder when several closely related files belong together — rather than appending the bulk of it into an existing “nearby” module. This is a default bias for reviewability, not a mandate to split every change.

- Existing files may gain a short import and a thin call site; they should not absorb a large new concern by default.
- Prefer a named home that matches the concern (`project/saved_trees/`, `panes/canvas/savedTrees/`) when the boundary is real.
- Stay in the existing file when the change is clearly the same concern (bugfix, rename, small extension) or would only create a micro-file without a clear boundary.
- Goal: avoid +500-line dumps into a random open file; do not invent files for ceremony.

This is this project's concrete application of `global-standards/CODE_STYLE_GUIDE.md` §2 (distinct concerns) and §6 (avoid unprompted layers — new files for real boundaries, not ceremony).

## Project structure

Root only holds shared resources spanning every project here (`docs/`, `tools/`, `CONVENTIONS.md`, `COLLABORATION.md`, `.gitignore` — these stay at root because Git/the tooling that reads them expect that, or because they're genuinely shared, not owned by one project) plus each self-contained project as its own top-level folder (currently `app/` only — see root `README.md`). A project's own runtime — `.venv/`, `requirements.txt`, `data/` — lives inside that project's own folder, never at the repository root; there is no root-level `.venv/` or `requirements.txt`. New source code belongs inside the relevant project's own subdirectory; source files must not be placed loose at the repository root.

See `docs/04-current-state.md` for which directories actually exist today and what's in each.

## Environment

- Each project here is self-contained: its own `.venv/`, its own `requirements.txt`, its own `data/` (see root `README.md`). For `app/`, that means `app/.venv/` and `app/requirements.txt` — there is no shared, repository-root virtual environment to activate instead.
- `app/backend/` is a Python package (`app/ui/` is a separate TypeScript prototype, not part of this package). Because its modules import from each other, project scripts must be run from `app/`'s own root using `-m` rather than as file paths — a plain file path will not work, since the imports rely on Python treating them as package members. `cd app/` first, then activate its environment once per terminal session (`source .venv/bin/activate`) to run things as plain `python -m ...` instead of `.venv/bin/python -m ...` each time. See `docs/04-current-state.md` for which modules actually exist and how to run them today.
- New dependencies: from within `app/`, install into its `.venv`, then refresh its own lockfile:
  ```bash
  .venv/bin/pip install <package>
  .venv/bin/pip freeze > requirements.txt
  ```
- Every project's own `.venv/` is git-ignored — never commit it.

## Security & privacy

Security/privacy by design: every architecture, storage, or sync decision explicitly considers its privacy/security trade-off *before* being made, not patched on afterward. Every deferral is written down with why in `docs/05-decisions.md`, and revisited when the risk profile changes (e.g. going from single-user local to multi-user/cloud).

This does not mean gold-plating an MVP — effort should match actual current risk. It means the trade-off is always explicit, never silent.

The long-term principles this implies (local-first, end-to-end encryption for any synced data) are architecture, not a coding convention — see `docs/03-architecture.md` § 5. Current security status (what's encrypted today, what isn't yet): see `docs/04-current-state.md`.

## LLM backend

LLM provider configuration must remain replaceable; provider-specific implementation details (which provider, which model, the current call site) belong in `docs/04-current-state.md` and `docs/05-decisions.md`, not here — keeping this file accurate whenever the provider changes would otherwise mean editing a coding-standards document every time a current-state fact changes.
