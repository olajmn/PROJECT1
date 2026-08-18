# backend

This is the agent's brain — the code that turns a goal into a plan, and
a plan into "what to do right now."

Named `backend` to match the architecture terminology in
`../docs/08-technical-architecture.md` (backend vs. future frontend), but
think of it as the agent itself: everything in here is what actually
does the thinking, planning, and remembering.

Run everything from the **project root**, using `-m` (see `../CONVENTIONS.md`
§ Environment for why):

| File | Responsibility | Run with |
|---|---|---|
| `goal_to_plan.py` | Goal → structured plan, and `replan()` (plan + feedback → updated plan). Both call the LLM | `.venv/bin/python -m backend.goal_to_plan` |
| `storage.py` | Save/load plans (and feedback) to/from `../data/plans.json` | (imported by others, not run directly) |
| `today.py` | Show just today's immediate action from the latest plan | `.venv/bin/python -m backend.today` |

## `devtools/` — personal tools, not the product's frontend

Same "agent vs. interface" distinction as everywhere else in this
project (see `../docs/08-technical-architecture.md`): these are just
ways for the project owner to interact with/inspect the agent during
development. Isolated in their own subpackage so it's obvious at a
glance which files are the agent and which are personal tooling.

| File | Responsibility | Run with |
|---|---|---|
| `devtools/view.py` | Generate a static HTML page of the full history (`data/view.html`) | `.venv/bin/python -m backend.devtools.view` |
| `devtools/app.py` | Local interactive web page (Flask) — set goals, give feedback, through a browser instead of the terminal. Then open http://127.0.0.1:5050 | `.venv/bin/python -m backend.devtools.app` |
| `devtools/templates/index.html` | The one page `app.py` serves |
| `devtools/static/style.css` | Styling for that page. Lives in `static/`, not loose in `devtools/`, because Flask serves *everything* in `static/` as raw downloadable files at `/static/...` — keeping it in its own folder means only the CSS is exposed that way, never `app.py`/`view.py` themselves |

See `../docs/08-technical-architecture.md` for the full architecture and
`../docs/09-mvp.md` for what's built vs. still planned.
