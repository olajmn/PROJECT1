# frontend (frozen reference copy)

> **Frozen reference (2026-09-11):** copied here verbatim from `current/frontend/` as a reference for v4's own, still-unbuilt `frontend/` - not wired to anything, not runnable as-is (it imports from `backend.goals.*`, which doesn't exist under v4's `backend/planning/` layout - see `docs/04-current-state.md` § 6), and not maintained going forward. `current/frontend/` remains the real, frozen prototype this was copied from; this copy exists only so v4's real `frontend/` (a separate, later task) can be built with this in view without reaching back into `current/`. The relative links below (`../docs/...`, `../CONVENTIONS.md`) are unchanged from the original and point to `current/`'s own siblings, not v4's - left as-is rather than rewritten, since rewriting them would misrepresent this as current, maintained documentation rather than a historical snapshot.

# frontend

The project's local web interface for interacting with/inspecting the
agent - not a separate future frontend concept, this IS the interface
layer (see `../docs/03-architecture.md` § Runtime architecture: the UI
and backend are separate layers, interfaces are replaceable clients).

Lives as a top-level sibling of `backend/`, not inside it (moved out of
`backend/` 2026-08-24, renamed from `devtools/` to `frontend/`
2026-08-30 once it had become the project's actual web layer rather
than a personal dev tool - see `../docs/03-architecture.md` § Long-term
architecture): this is the channel a human talks TO the agent through
(the USER node in that doc's long-term diagram), not part of the
agent's own cognition. It still imports directly from `backend/`
(`app.py` calls `create_goal()`, `build_goal_overview()`, etc.) - it's
the only functioning way to actually use the agent today, just not a
permanent part of it.

Run everything from the **project root**, using `-m` (see
`../CONVENTIONS.md` § Environment for why):

```
.venv/bin/python -m frontend.app
```

Then open http://127.0.0.1:5050.

## Structure

`app.py` splits into a Conversation entry point and five work areas,
tied together by a shared navigation bar - each with its own route and
its own `templates/` subfolder:

| Work area | Route | View function | Page template | Content partial |
|---|---|---|---|---|
| Conversation | `GET /` | `conversation()` | `index.html` | `conversation/_conversation.html` |
| Set Goal | `GET /set-goal`, `POST /set-goal` | `set_goal_page()`, `new_goal()` | `set_goal/page.html` | `set_goal/_goal_form.html` |
| Vision | `GET /vision`, `POST /vision` | `vision_page()`, `new_vision()` | `vision/page.html` | `vision/_vision_form.html` |
| Active | `GET /active` | `active_page()` | `active/page.html` | `active/_active_view.html` |
| Completed | `GET /completed` | `completed()` | `completed_goal/completed.html` | `completed_goal/_completed.html` |
| History | `GET /history` | `history()` | `history/history.html` | `history/_history_list.html` |

Five more POST-only routes act on an existing Goal or Vision rather
than showing a page of their own - `POST /feedback`, `POST /step`,
`POST /goal-vision`, and `POST /goal-cancel` redirect back to Active
afterward; `POST /vision-archive` redirects back to Vision.

Conversation is the agent's entry point (see
`templates/conversation/_conversation.html`) - a static placeholder
today, not yet wired to any real intent parsing; the other five are
where a user (or, eventually, the agent on the user's behalf) actually
operates on Goal/Vision/Plan data. See
`../docs/03-architecture.md` § Vision for why Vision is its own work
area rather than part of Set Goal.

### Navigation

`templates/navigation/_navbar.html` - the six work-area links, shown
on every page above, included rather than copied. Its CSS lives
separately in `css/navbar.css`, not in `style.css`, for the same
reason the template is its own file: the navbar is navigation, not a
domain or a component.

### Components

Rendered inside a work area, no route of their own:

- `_active_goal.html` + `active_goal/` (one active goal's card - Goal /
  Plan / Timeperiod / Task / Steps / Conversation, each its own file)
  - used inside Active.
- `_plan_entry.html` (one plan record as a plain key:value block, not
  a conversation thread) - shared by Completed and History, so it
  stays at the top level rather than living inside either one.

### CSS

| File | Responsibility |
|---|---|
| `css/style.css` | Global/base styling, layout (`.layout`/`.col`), and every work-area/component style not specific to the navbar |
| `css/navbar.css` | The navigation bar only (`.navbar`, `.nav-link`, `.nav-link-current`) |

Both live in `css/` (`static_folder="css"`, not the default `static/`
name), not loose in `frontend/`, because Flask serves *everything* in
that folder as raw downloadable files at `/static/...` - keeping it
separate means only the CSS is exposed that way, never `app.py` itself.

### view_data/

| File | Responsibility |
|---|---|
| `view_data/plan_horizons.py` | UI display data for Plan's time horizons - labels and ordering, never read by Plan's own logic |
| `view_data/text_formatting.py` | Pure text formatting for templates (joining/splitting plan and message text for display) - no backend/domain dependency |
| `view_data/goal_overview.py` | View-data preparation for the goal-overview pages (active/completed split, Vision grouping) - not a general Goal/Vision capability |

Already-decided backend information shaped for `templates/` to render,
not the views themselves and not a domain capability. Split into its
own package 2026-08-30, once it was clear the three shared one
responsibility distinct from both `app.py` (routing) and `templates/`
(the actual HTML/Jinja).

## History

A standalone static-HTML-snapshot script (`view.py`, generating
`data/view.html` without needing the Flask server running) existed
2026-08-18 through 2026-08-24 - removed once `data/view.html` sat
untouched for 6 days next to the live, always-current `/history` page,
the evidence that its one advantage (no server needed) wasn't actually
being used. See `../docs/05-decisions.md`, 2026-08-18, for why it was
built.

The single combined landing page (everything - Set Goal, Vision,
Active - stacked on `index.html`) was split into the work-area
structure above; see `../docs/06-development.md` for that change.

See `../docs/03-architecture.md` for the full architecture and
`../docs/02-product.md` for what's built vs. still planned.
