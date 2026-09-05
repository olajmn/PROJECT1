# personal-ai-agent

An agent that turns a stated goal into a plan, a plan into a single next
action, and user feedback into a revised plan — `goal → plan → action →
feedback → replan`. Not a todo list generator: the loop is meant to keep
running, deciding what should happen next rather than only producing a
plan once.

## Status

Prototype 0.1. The full loop above is closed end-to-end through a local
web UI; the LLM call, temporal interpretation, and persistence all run
today. Memory, retrieval/knowledge, and any external action are not
built yet.

This section is deliberately brief and will drift out of date quickly.
For the current, maintained picture of what's built / half-built / not
built, see [`docs/04-current-state.md`](docs/04-current-state.md).

## Architecture

The backend is organized around four categories, not one folder-per-feature:

| Category | Question it answers | Example |
|---|---|---|
| **Domain** | What does the system operate on? | Goals, Planning, Time |
| **Faculty** | What can the agent understand or interpret, reusably? | Temporal understanding (`foundation/time/`) |
| **Infrastructure** | What moves or stores data without understanding it? | `infrastructure/data_persistence.py` |
| **Interface** | How does a human reach the agent? | `frontend/` |

A Domain-to-Faculty relationship is not automatic: `time/` is the only
Domain that has produced an established Faculty (temporal
understanding) so far. Full definitions, the domain table, and the
long-term architecture are in
[`docs/03-architecture.md`](docs/03-architecture.md).

## The agent vs. the development framework

`backend/` is the agent, by architectural intent — the Domains that
define goal → plan → action → feedback → replan (`goals/`, `planning/`,
`foundation/`) live there. In the current implementation, part of that
loop's control flow — which kind of feedback a note is, and whether it
triggers `replan()` — is decided inside `frontend/app.py`'s routes
rather than inside `backend/` itself.

Everything else supports building or verifying the agent:

- `frontend/` — a local Flask UI for talking to the agent through a
  browser. Meant as a client of the backend, not a component of it —
  though today it also carries some of the feedback→replan routing
  logic described above.
- `tools/` — standalone dev utilities (`project_check.py`,
  `docs_check.py`, `docs_lint.py`). No runtime relationship to the agent.
- `docs/` — the project's documentation vault (architecture, decisions,
  development history).
- `data/` — local, git-ignored storage for plans and history.

## Getting started

Requires Python 3 and [Ollama](https://ollama.com) running locally.

```bash
# 1. Install and start Ollama, then pull the model the agent calls:
ollama pull llama3.1:8b
brew services start ollama   # or otherwise ensure the Ollama service is running

# 2. Set up the Python environment (from the project root):
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Run the local web UI (must run from the project root, with -m):
.venv/bin/python -m frontend.app
```

No cloud LLM, no external API key, and no network access is required —
the agent calls a model running on the same machine.

## Verification layer

`tools/project_check.py` is a deterministic scan, not an understanding
of the project. It checks git status; whether a fixed list of
explicitly named entry-point modules — not every file under `backend/`
and `frontend/` — still import cleanly; and, as a separate mechanical
check, `pyflakes` output for `backend/` and `frontend/`. It also runs
`docs_check.py` (the `docs/` vault's own structural integrity —
expected files, `[[wikilinks]]`, headings) as a sub-check, and
separately scans code comments/docstrings under `backend/`,
`frontend/`, and `tools/` for `backend/…`/`frontend/…` `.py` paths that
no longer resolve to a real file. Nothing it reports is a judgment
about whether the project's design is correct. Run it before trusting
a claim about current state:

```bash
.venv/bin/python tools/project_check.py
```

See [`COLLABORATION.md`](COLLABORATION.md) for why this exists and how
its output is meant to be used.

## Documentation map

| File | Answers |
|---|---|
| [`docs/00-project-brief.md`](docs/00-project-brief.md) | What is this project trying to become? |
| [`docs/01-research.md`](docs/01-research.md) | What problem is this, and what already exists outside this project? |
| [`docs/02-product.md`](docs/02-product.md) | What is the concrete product — flows, features, MVP scope? |
| [`docs/03-architecture.md`](docs/03-architecture.md) | How is the agent structured, and why? |
| [`docs/04-current-state.md`](docs/04-current-state.md) | What is true right now? |
| [`docs/05-decisions.md`](docs/05-decisions.md) | Why was it built this way? |
| [`docs/06-development.md`](docs/06-development.md) | What happened, and when? |
| [`COLLABORATION.md`](COLLABORATION.md) | How a session or developer should work with this project |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Code and documentation style |
