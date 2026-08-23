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
| `plan.py` | Goal → structured plan, and `replan()` (plan + feedback → updated plan). Both call the LLM | `.venv/bin/python -m backend.plan` |
| `goal.py` | Goal identity/grouping - `get_board()`, `get_latest_for_goal()`, `get_history_for_goal()` | (imported by others, not run directly) |
| `timeperiod.py` | Understanding "when" a plan should span - resolves/describes recognized day segments and week/month/year phrases into a real clock window or calendar date range, honest about what it can't parse | (imported by others, not run directly) |
| `timesegments.py` | The recognized time phrases/patterns themselves (`DAY_SEGMENTS`, `PERIOD_PHRASES`, etc.) - pure data, no logic; `timeperiod.py` is the logic that uses it | (imported by others, not run directly) |
| `outcome_classifier.py` | Deterministic (no LLM) classification of free-text feedback into done/not_done/in_progress/goal_done - the logic; `outcome_phrases.py` is the data it uses | (imported by others, not run directly) |
| `outcome_phrases.py` | The recognized feedback phrases themselves (`GOAL_DONE_PHRASES`, `RULES`, etc.) - pure data, no logic | (imported by others, not run directly) |
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
| `devtools/view.py` | Generate a static HTML snapshot of the full history (`data/view.html`) — reuses `app.py`'s Flask app + `goal_log/history.html` template rather than hand-building HTML | `.venv/bin/python -m backend.devtools.view` |
| `devtools/app.py` | Local interactive web page (Flask) — set goals, give feedback, through a browser instead of the terminal. Also exposes `render_history_page()`, shared with `view.py`. Then open http://127.0.0.1:5050 | `.venv/bin/python -m backend.devtools.app` |
| `devtools/html/` | Every template, one folder per section (`Flask(..., template_folder="html")`, not the default `templates/` name) - `index.html` (`/`), `_active_goal.html` + `active_goal/` (one active goal's card: Goal/Plan/Timeperiod/Task/Steps/Conversation, split into their own files), `set_goal/` (the goal-creation form), `completed_goal/` (`/completed`, finished goals only), `goal_log/` (`/history`, every record ever saved) |
| `devtools/css/style.css` | Styling for every page above. Its own folder (`static_folder="css"`, not the default `static/` name), not loose in `devtools/`, because Flask serves *everything* in that folder as raw downloadable files at `/static/...` — keeping it separate means only the CSS is exposed that way, never `app.py`/`view.py` themselves |

See `../docs/08-technical-architecture.md` for the full architecture and
`../docs/09-mvp.md` for what's built vs. still planned.
