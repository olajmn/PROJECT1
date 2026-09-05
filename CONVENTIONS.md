# Project Conventions

Technical standards for this codebase. Applies going forward.

## Contents

- Language
- Interface style
- Documentation neutrality
- Code documentation
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

- Code comments, docstrings, and `docs/` files state the reasoning or consequence itself, not the personal narrative of how/when/by whom it was noticed — "X breaks without Y" instead of naming the real screenshot that happened to reveal it, "the goal was X" instead of framing X as something personally wanted. Already applied to code comments (see git history, "Depersonalize comments: state facts/consequences, not discovery narrative"); the same standard applies to everything in `docs/`, since it's the material most likely to be read by someone outside this project one day. Doesn't apply to genuinely dated, historical log entries where a specific date/event is the actual point (`docs/06-development.md`, `docs/05-decisions.md`'s "Date:" field) — those record when something happened; only the surrounding voice gets depersonalized, not the fact that it happened on a given day.
- "The user" as a term still refers to the *product's* end-user where that's the actual subject (e.g. "the user's own device holds a complete copy of their data") — this rule is about not narrating this project's own build process as a personal story, not about avoiding the word.
- The exact, checkable patterns this rule means are defined once, in `tools/docs_lint.py` (`_CONFIRMED_PATTERNS`/`REVIEW_PATTERN`) — not restated here, same as `GOAL_DONE_PHRASES`/`DAY_SEGMENTS` aren't reproduced in prose anywhere outside the code that owns them. Run it (`.venv/bin/python3 tools/docs_lint.py`) rather than checking by eye; update the patterns there, not this paragraph, when a new case of the same problem turns up.

## Code documentation

Source-code Contents (what a file's navigation block should contain, and when one is warranted) is defined in `global-standards/CODE_STYLE_GUIDE.md` §1-§2, not restated here. Document-oriented Contents is `global-standards/DOCUMENTATION_STYLE_GUIDE.md`'s job; `global-standards/_CONTENT_HIERARCHY.md` covers heading-hierarchy notation where that level of detail is needed. This project has no Contents rule of its own beyond those.

## Project structure

Root only holds folders + standard project metadata files (`.gitignore`, `requirements.txt`, `CONVENTIONS.md` — these stay at root because Git/pip expect them there). New source code belongs in an appropriate subdirectory; source files must not be placed loose at the repository root.

See `docs/04-current-state.md` for which directories actually exist today and what's in each.

## Environment

- Dependencies are installed in a project-local virtual environment at `.venv/`, not system-wide. This avoids conflicts between the multiple Python installations present on this machine.
- `backend/` and `frontend/` are Python packages. Because their modules import from each other, project scripts must be run from the repository root using `-m` rather than as file paths — a plain file path will not work, since the imports rely on Python treating them as package members. Activate the environment once per terminal session (`source .venv/bin/activate`) to run things as plain `python -m ...` instead of `.venv/bin/python -m ...` each time. See `docs/04-current-state.md` for which modules actually exist and how to run them today.
- New dependencies: install into `.venv`, then refresh the lockfile:
  ```bash
  .venv/bin/pip install <package>
  .venv/bin/pip freeze > requirements.txt
  ```
- `.venv/` is git-ignored — never commit it.

## Security & privacy

Security/privacy by design: every architecture, storage, or sync decision explicitly considers its privacy/security trade-off *before* being made, not patched on afterward. Every deferral is written down with why in `docs/05-decisions.md`, and revisited when the risk profile changes (e.g. going from single-user local to multi-user/cloud).

This does not mean gold-plating an MVP — effort should match actual current risk. It means the trade-off is always explicit, never silent.

The long-term principles this implies (local-first, end-to-end encryption for any synced data) are architecture, not a coding convention — see `docs/03-architecture.md` § Architectural principles. Current security status (what's encrypted today, what isn't yet): see `docs/04-current-state.md`.

## LLM backend

LLM provider configuration must remain replaceable; provider-specific implementation details (which provider, which model, the current call site) belong in `docs/04-current-state.md` and `docs/05-decisions.md`, not here — keeping this file accurate whenever the provider changes would otherwise mean editing a coding-standards document every time a current-state fact changes.
