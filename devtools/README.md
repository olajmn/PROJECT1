# devtools

Personal tools for interacting with/inspecting the agent during
development - not the product's real frontend (see
`../docs/03-architecture.md` § Runtime architecture: the UI and
backend are separate layers, interfaces are replaceable clients).

Lives as a top-level sibling of `backend/`, not inside it (moved
2026-08-24, see `../docs/03-architecture.md` § Long-term architecture):
this is the channel a human talks TO the agent through (the USER node
in that doc's long-term diagram), not part of the agent's own
cognition. It still imports directly from `backend/` (`app.py` calls
`generate_plan()`, `get_latest_for_all_goals()`, etc.) - it's the only
functioning way to actually use the agent today, just not a permanent
part of it.

Run everything from the **project root**, using `-m` (see
`../CONVENTIONS.md` § Environment for why).

| File | Responsibility | Run with |
|---|---|---|
| `app.py` | Local interactive web page (Flask) — set goals, give feedback, through a browser instead of the terminal, including a `/history` page showing every record ever saved. Then open http://127.0.0.1:5050 | `.venv/bin/python -m devtools.app` |
| `html/` | Every template, one folder per section (`Flask(..., template_folder="html")`, not the default `templates/` name) - `index.html` (`/`), `_active_goal.html` + `active_goal/` (one active goal's card: Goal/Plan/Timeperiod/Task/Steps/Conversation, split into their own files), `_plan_entry.html` (one plan record as a plain key:value block, not a conversation thread - shared by `completed_goal/` and `goal_log/` below), `set_goal/` (the goal-creation form), `completed_goal/` (`/completed`, finished goals only), `goal_log/` (`/history`, every record ever saved) |
| `css/style.css` | Styling for every page above. Its own folder (`static_folder="css"`, not the default `static/` name), not loose in `devtools/`, because Flask serves *everything* in that folder as raw downloadable files at `/static/...` — keeping it separate means only the CSS is exposed that way, never `app.py` itself |

A standalone static-HTML-snapshot script (`view.py`, generating
`data/view.html` without needing the Flask server running) existed
2026-08-18 through 2026-08-24 - removed once `data/view.html` sat
untouched for 6 days next to the live, always-current `/history` page,
the evidence that its one advantage (no server needed) wasn't actually
being used. See `../docs/05-decisions.md`, 2026-08-18, for why it was
built.

See `../docs/03-architecture.md` for the full architecture and
`../docs/02-product.md` for what's built vs. still planned.
