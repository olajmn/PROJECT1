# PROJECT1

A local app for building things out of nodes — each node an object with
its own identity — with a conversation that works on the structure.

## What is where

| Path | What |
|---|---|
| `app/` | The application: Python backend, TypeScript UI, local data |
| `docs/` | The project's documentation (an Obsidian vault) |
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

## Run it

```bash
cd app && .venv/bin/python -m server
```

Then open http://localhost:8000/. Tests, checks, and the UI build:
`docs/04-current-state.md` § 1, or `/full-check` in Claude Code.
