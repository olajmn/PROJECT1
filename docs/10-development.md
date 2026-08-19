# 10 — Development Log

> Phase 7-9 in [[00-project-brief]]. Running log, newest first.

## 2026-08-19 (latest x2)

- Found via the first real test goal ("take shower", duration "any
  time before i got to bed") that day-segment resolution missed a 4th
  real category: a deadline tied to a personal routine event (bedtime),
  not a clock time. Added `_DEADLINE_RE` (a tolerant regex, not a fixed
  phrase list - the first attempt with exact phrases missed "before i
  **got to** bed") so `describe_duration()` names this case honestly
  ("recognized as a same-day deadline - actual time unknown, not
  grounded") instead of lumping it into unexamined free text.
  Deliberately does NOT invent a clock time for it, unlike day segments
  - there's no real bedtime to compute.

## 2026-08-19 (latest)

- Added a "Goal complete" button/state: the user can now explicitly
  mark a whole goal done (new `completed` field on each record) instead
  of the agent having to guess it from a missing `right_now` - built
  after a real test run (`ta en dusj`) hit exactly that: the model
  returned `right_now: null` with no way to say "actually, I'm done."
  `index.html` shows a plain confirmation card instead of an empty
  action box when the latest record is completed; a defensive fallback
  also covers the same `null` case for goals *not* marked complete.
- New `/board` view (embedded on the front page in a two-column layout,
  plus standalone at `/board`): groups goal history by latest known
  state into "Active"/"Completed", since a goal is a chain of records
  sharing the same goal text, not its own stored entity
  (`storage.get_board()`).
- Interface redesign, in response to user feedback that the UI looked
  more confident/"friendly" than the underlying data warrants: switched
  to a plain, monospace `key: value` display (no colored boxes, no
  rounded corners, outlined not filled buttons) across the whole page;
  `plan:` shown as a genuinely nested key (matching the real stored
  shape) instead of flattened; every line marked `# given` (verbatim
  user input) or `# generated, unverified` (LLM output) so reliability
  isn't visually implied where none exists. No emojis anywhere, per
  explicit user preference (also see global Claude preference, not
  project-specific).
- Day-segment duration resolution: `goal_to_plan.py` now recognizes a
  small hardcoded set of day segments (morning/afternoon/evening/night,
  Norwegian included) and grounds them in a real computed clock window
  for today (e.g. "kveld" → "17:00-23:00") instead of handing the raw
  word to the model - concrete first piece of "temporal awareness"
  beyond just passing the current timestamp. Plain lengths ("30
  minutes") and fully open text ("before my trip") still pass through
  unexamined, as before. `describe_duration()` shows which case applies
  directly in the UI, replacing a static comment.
- Found and logged a severe, reproducible reliability issue: Norwegian
  goal text causes `llama3.1:8b` to produce answers completely
  disconnected from the goal (e.g. inventing "German" content from
  nowhere); the identical goal in English produced grounded, sensible
  answers. See [[11-experiments]] and [[12-decisions]] for the
  write-goals-in-English decision this led to.
- Board cleanup: all 7 pre-existing active goals marked complete (new
  records, nothing deleted - 32 history entries intact) to give a clean
  "Active" board before starting real usage testing.

## 2026-08-19

- Temporal grounding: `goal_to_plan.py` now sends the real current
  date/time (`_now_str()`) to the model on every `generate_plan()` and
  `replan()` call, so "right now" is grounded in the actual moment
  instead of the model having no sense of time. First concrete step
  toward the still-unbuilt "Temporal awareness" item in
  [[08-technical-architecture]].
- Added an optional free-text `duration` field to the "set a goal" form
  (e.g. "30 minutes", "this week") — passed through to the model and
  stored on the record. Deliberately free text, no fixed dropdown
  options, per user preference.
- Prompt change: the model now returns JSON `null` for any horizon
  (`one_year`/`one_month`/`this_week`) that isn't relevant to the
  goal's scope, instead of inventing a value ("Unknown" or a
  hallucinated specific) just to fill the field. `right_now` is always
  filled in. Tested: consistent across repeated calls; one noted
  inaccuracy where a 3-month goal skipped `one_month` — a model
  calibration limitation, not a code bug.
- Bug found and fixed: `/feedback` wasn't carrying the goal's
  `duration` through to `replan()`/`save_plan()`, so it silently
  reverted to `null` after the first feedback round. Fixed in
  `backend/devtools/app.py`.
- `index.html` now shows the broader plan (whichever of
  `this_week`/`one_month`/`one_year` came back non-null) above "Right
  now", not just in `/history` — so a longer-duration goal's larger
  arc is visible on the page you actually act from day to day, while
  short-duration goals (which have no broader plan) show only "Right
  now" as before.
- UI cleanup: "Set a goal" moved above the current goal/feedback card,
  simplified from two near-duplicate form blocks to one shared block;
  added light styling (`card-muted`, `duration-tag`) — personal-tool
  readability, not product polish, see [[12-decisions]].
- Logged a user-proposed idea (folder-per-time-period storage + a
  scanning planning algorithm over it) into
  [[08-technical-architecture]] § Memory & Data Architecture and
  [[13-ideas-parking-lot]] — not built, matches the existing
  "testing over further ideation" decision in [[12-decisions]].

## 2026-08-18 (latest x5)

- Cleanup pass via `/code-review` + `/simplify` on `backend/` (5 parallel
  agents: correctness, reuse, simplification, efficiency, altitude —
  see [[12-decisions]] for the full list of what was fixed vs. skipped).
  Highlights: `storage.py` now owns the plan schema (`PLAN_KEYS`) and
  normalizes legacy string-format plans once, at the source, instead of
  every reader special-casing them; atomic writes to `plans.json`;
  `view.py`'s hand-built HTML replaced with a proper Jinja template
  (`history.html`), fixing an HTML-escaping gap the templated `index.html`
  didn't have; Flask routes no longer crash on missing form fields or an
  empty history. Tested: `today.py`, `view.py`, and `app.py` (including
  the fixed edge cases and the XSS-escaping fix) all re-verified working.

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
