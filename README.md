# project010

A local app for building things out of nodes — each node an object with
its own identity — with a conversation that works on the structure. In
practice: you build a project as a tree of parts (a building, a training
plan, a folder on disk), and a chat beside it answers questions about
that project and the part you select.

**Live demo:** https://demo-one.fly.dev — ask me for the password. Each
visitor gets their own copy of two example projects. How the demo works:
`docs/demo.md`.

**Built with:** Python (standard-library HTTP server, no framework),
TypeScript (no framework, no bundler), plain JSON files for storage, and
a language model through Ollama locally or OpenRouter in the demo.

## Where to start reading

1. `docs/00-project-brief.md` — what the project is
2. `docs/03-architecture.md` — how it is built
3. `docs/05-decisions.md` — what was decided, and why

## What is where

| Path | What |
|---|---|
| `app/` | The application: Python backend, TypeScript UI, local data |
| `docs/` | The project's documentation (Markdown; `[[name]]` links follow Obsidian's style) |
| `tools/` | Checks for the repository and the docs |
| `global-standards/` | General, project-independent style and collaboration guides |
| `TODO.md` | What is being worked on, what is open, and ideas |
| `CONVENTIONS.md` | This project's technical conventions |
| `COLLABORATION.md` | How to work in this project: which doc answers what, which checks to run |

## Docs

| Doc | Answers |
|---|---|
| `docs/00-project-brief.md` | What the project is |
| `docs/01-research.md` | What to look for outside it |
| `docs/02-product.md` | The foundation and the app |
| `docs/03-architecture.md` | How it is built |
| `docs/04-current-state.md` | What is true now |
| `docs/05-decisions.md` | What was decided, and why |
| `docs/ui.md` | The screen, and where UI code lives |
| `docs/demo.md` | The public demo: how it works and how to deploy it |

## Run it

Needs Python 3.14, Node.js, and [Ollama](https://ollama.com) with the
model `qwen3.5:9b` (`ollama pull qwen3.5:9b`). Once, from `app/`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ui && npm install && npm run build && cd ..
```

Then, from `app/`:

```bash
.venv/bin/python -m server
```

and open http://localhost:8000/. Tests, checks, and the UI build:
`docs/04-current-state.md` § 1, or `/full-check` in Claude Code.
