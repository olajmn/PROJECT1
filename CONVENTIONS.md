# Project Conventions

Technical standards for this codebase. Applies to every file going forward.

## Language

- **Everything in the repository is written in English**: code
  (variable/function names, comments, docstrings, log/print strings,
  prompts embedded in code) and all files in `docs/` (project brief,
  research, decisions, etc.).
- Live conversation with the assistant while working on the project can
  still happen in Norwegian — this rule covers files that get committed,
  not the chat itself.

## Interface style

- No emojis anywhere in the UI (button labels, status text, headings)
  or in generated content. Plain text only.

## Documentation neutrality

- Code comments, docstrings, and `docs/` files state the reasoning or
  consequence itself, not the personal narrative of how/when/by whom
  it was noticed - "X breaks without Y" instead of naming the real
  screenshot that happened to reveal it, "the goal was X" instead of
  framing X as something personally wanted.
  Already applied to code comments (see git history, "Depersonalize
  comments: state facts/consequences, not discovery narrative"); the
  same standard applies to everything in `docs/`, since it's the
  material most likely to be read by someone outside this project one
  day. Doesn't apply to genuinely dated, historical log entries where
  a specific date/event is the actual point (`docs/10-development.md`,
  `docs/11-experiments.md`, `docs/12-decisions.md`'s "Date:" field) -
  those record when something happened; only the surrounding voice
  gets depersonalized, not the fact that it happened on a given day.
- "The user" as a term still refers to the *product's* end-user where
  that's the actual subject (e.g. "the user's own device holds a
  complete copy of their data") - this rule is about not narrating
  this project's own build process as a personal story, not about
  avoiding the word.
- The exact, checkable patterns this rule means are defined once, in
  `tools/docs_lint.py` (`_CONFIRMED_PATTERNS`/`REVIEW_PATTERN`) - not
  restated here, same as `GOAL_DONE_PHRASES`/`DAY_SEGMENTS` aren't
  reproduced in prose anywhere outside the code that owns them. Run it
  (`.venv/bin/python3 tools/docs_lint.py`) rather than checking by eye;
  update the patterns there, not this paragraph, when a new case of
  the same problem turns up.

## Project structure

Root only holds folders + standard project metadata files (`.gitignore`,
`requirements.txt`, `CONVENTIONS.md` - these stay at root because Git/pip
expect them there). All source code lives in subfolders, never loose at
root.

```
backend/            The agent itself - see backend/README.md
devtools/           Personal dev tools (web UI) - not the product's frontend, moved
                    out of backend/ 2026-08-24 (see devtools/README.md): this talks
                    TO the agent, it isn't part of the agent's own cognition
data/               Local storage, git-ignored (personal data - see Security & Privacy below)
docs/               Obsidian vault - product/research/decision docs (see docs/00-project-brief.md)
tools/              Standalone dev utilities with no runtime relationship to the
                    agent (e.g. tools/architecture_mapper)
```

## Environment

- Dependencies are installed in a project-local virtual environment at
  `.venv/`, not system-wide. This avoids conflicts between the multiple
  Python installations present on this machine.
- `backend/` and `devtools/` are each a real Python **package**
  (`backend/__init__.py`, `devtools/__init__.py`), because files inside
  them import from each other, and `devtools/app.py` imports from
  `backend/` (e.g. `app.py` needs `storage.py`). This means every
  script must be run **from the project root**, using `-m` and dots
  instead of a file path:
  ```bash
  .venv/bin/python -m backend.agent.specialized.plan
  .venv/bin/python -m backend.agent.specialized.today
  .venv/bin/python -m devtools.app
  ```
  `python backend/agent/specialized/plan.py` (a plain file path) will NOT work
  anymore - the imports inside these files rely on Python treating them
  as package members, which only happens via `-m`.
  Or activate the environment once per terminal session:
  ```bash
  source .venv/bin/activate
  python -m backend.agent.specialized.today
  ```
- New dependencies: install into `.venv`, then refresh the lockfile:
  ```bash
  .venv/bin/pip install <package>
  .venv/bin/pip freeze > requirements.txt
  ```
- `.venv/` is git-ignored — never commit it.

## Security & Privacy

Security/privacy by design: every architecture, storage, or sync
decision explicitly considers its privacy/security trade-off *before*
being made, not patched on afterward. Every deferral is written down
with why in `docs/12-decisions.md`, and revisited when the risk profile
changes (e.g. going from single-user local to multi-user/cloud) — see
`docs/08-technical-architecture.md` § Security & Privacy Goals.

This does not mean gold-plating an MVP — effort should match actual
current risk (e.g. no password-encrypted local file yet while the
project is single-user and disk-level encryption already covers the
realistic threat). It means the trade-off is always explicit, never
silent.

Two standing long-term goals, already documented:

1. End-to-end encryption for any synced/cloud data (Bitwarden-style —
   server never sees plaintext)
2. Local-first architecture so no single company can lock the user out
   of their own data (the user's device is always the source of truth;
   any sync server is a replaceable relay, never the owner of the data)

## LLM backend

- Currently using **Ollama** (`llama3.1:8b`) running locally — no API key,
  no cost, no internet required. Started via `brew services start ollama`.
- The `anthropic` package is also installed and kept up to date in
  `requirements.txt`, so the project can switch to Claude (`claude-opus-5`)
  later by setting `ANTHROPIC_API_KEY` and swapping the client — no
  reinstall needed. See `backend/agent/specialized/plan.py` for the current call site.
