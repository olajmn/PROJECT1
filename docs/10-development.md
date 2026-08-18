# 10 — Development Log

> Phase 7-9 in [[00-project-brief]]. Running log, newest first.

## 2026-08-18 (latest x4)

- Initialized git, verified `.gitignore` correctly excludes `data/`
  (personal goals/plans), `.venv/`, `__pycache__/`, `.DS_Store` before
  first commit. Created private GitHub repo
  ([github.com/olajmn/personal-ai-agent](https://github.com/olajmn/personal-ai-agent))
  and pushed initial commit (Prototype 0.1, full loop closed).

## 2026-08-18 (latest, latest, latest)

- Split off `backend/devtools/` (proper Python subpackage) for the
  personal dev tools (`app.py`, `view.py`, `templates/`), separate from
  the agent itself. `backend/` is now a real package
  (`backend/__init__.py`), so **every** script's run command changed to
  `-m` form, e.g. `.venv/bin/python -m backend.today` instead of
  `.venv/bin/python backend/today.py` — see `../CONVENTIONS.md`.
- Correction logged for transparency: initially claimed only the moved
  files needed import changes; turned out `goal_to_plan.py`/`today.py`
  needed their internal `from storage import ...` changed to
  `from backend.storage import ...` too, since they're now accessed as
  package members via `app.py`. Fixed and re-tested end-to-end.

## 2026-08-18 (latest, latest)

- Built `backend/app.py`: local interactive web page (Flask) — set a
  goal, see "right now", give feedback via buttons/text. Closes
  Prototype 0.1's full loop (see [[09-mvp]], [[04-hypothesis]])
- Added `replan()` to `goal_to_plan.py`: takes the previous plan + user
  feedback, asks the LLM for an updated plan
- Extended `storage.save_plan()` with an optional `feedback` field
- Installed Flask into `.venv/` (was floating in system Python before —
  now properly isolated per [[../CONVENTIONS.md]])
- Tested end-to-end via curl: goal → plan → feedback ("too busy today")
  → replan produced a smaller, easier next action, as intended

## 2026-08-18 (latest)

- Integrated a parallel ChatGPT discussion into the vault: refined
  hypothesis as a closed loop ("Prototype 0.1"), added temporal
  awareness + memory/data architecture ideas to [[08-technical-architecture]],
  added new parking-lot items (voice, web UI, aggregation, reflection),
  logged two decisions in [[12-decisions]] (agent-not-planner-app reframe,
  testing over further ideation). No code changed in this pass.

## 2026-08-18 (even even later)

- Reorganized: all Python code moved into `backend/` (a "src layout" -
  root now holds only folders + standard project metadata files like
  `.gitignore`/`requirements.txt`, which stay at root because Git/pip
  expect them there). Added `backend/README.md`. Fixed `storage.py`'s
  data path for the new nesting level. Verified no data lost.

## 2026-08-18 (even later)

- Switched `goal_to_plan.py` to structured JSON output (`format="json"`
  in Ollama) instead of free text — keys: `one_year`, `one_month`,
  `this_week`, `right_now`
- Added `today.py`: prints just `right_now` from the latest saved plan —
  the "zoom all the way in" step from [[00-project-brief]] §2

## 2026-08-18 (later)

- Added `storage.py`: goal+plan history persisted to `data/plans.json`
  (append-only, not overwritten). See [[12-decisions]] for why history
  over overwrite, and the privacy trade-off of unencrypted local JSON.
- Added `data/` to `.gitignore` — personal goals/plans must never be
  committed
- Added `docs/08-architecture.drawio` — full visual architecture diagram

## 2026-08-18

- Set up `goal_to_plan.py` (v0.1): goal → plan via LLM, no storage yet
- Tried Anthropic Claude (`claude-opus-5`) first — invalid API key (401)
- Switched to a local LLM via **Ollama** (`llama3.1:8b`) — no key, no
  cost, runs on the local machine. See [[12-decisions]]
- Cleaned up the Python environment: created `.venv/` to avoid conflicts
  between two Python 3.14 installations on the machine
- Set a code convention: all code and docs in English, see `../CONVENTIONS.md`
- Set up the `docs/` folder (this structure) as an Obsidian vault

## See also

- [[09-mvp]]
- [[11-experiments]]
