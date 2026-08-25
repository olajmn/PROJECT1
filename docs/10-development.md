# 10 — Development Log

> Phase 7-9 in [[00-project-brief]]. Running log, newest first.

## 2026-08-25 (latest)

- Picked "Semantic understanding of time" off [[SESSION-TODO]]'s
  five-item list (the other four stay parked). Built the first,
  narrower half of the idea in [[14-semantic-time]]: `relative_length()`
  in a new `backend/agent/distributed/temporal/relative_time.py` - given
  two duration strings, returns whether the first is "short"/"medium"/
  "long" relative to the second (e.g. the goal's overall duration),
  via a fixed, hardcoded ratio table, not a model call. Placed inside
  the Time faculty rather than a new one - it needs no knowledge of
  what either span is FOR, only their relative magnitude; the doc's
  own "Future hook" note (see `temporal/__init__.py`'s history)
  had already anticipated this. The harder "activity-specific
  meaning" half of the original idea (is 45 minutes short or long FOR
  RUNNING specifically) is untouched - stays open, see
  [[14-semantic-time]]. Not yet wired into any caller (`plan.py`,
  `replan()`, the UI) - exists as a capability, not yet used.
- `timesegments.py` split: raw time-unit constants (`SECONDS_PER_MINUTE`,
  `MONTH_DAYS`, etc.) moved to a new sibling `timeunits.py` - a
  different kind of fact (never matched against typed text, unlike
  `timesegments.py`'s remaining phrase-recognition tables). Sections
  renumbered 1-4 accordingly. Both renamed `time_segments.py`/
  `time_units.py` later the same day, for consistency with every other
  multi-word file in the package (`phrase_matching.py` etc.).
- `agent/distributed/timeperiod/` renamed `temporal/` (19 files
  referenced the old name, all updated - imports, docs, `README.md`).
  Reasoning: "period" only fit part of what the package does (point-
  in-time and duration recognition, now also `relative_time.py`'s magnitude
  comparison); "Temporal" was already the project's own word for this
  (`docs/08-technical-architecture.md`'s "Temporal awareness -> the
  Time faculty" mapping, "Temporal grounding" in this log's 2026-08-19
  entry) - removes the recurring "Time (`timeperiod/`)" translation
  every doc mention needed. `time/` was considered and rejected -
  shadows Python's stdlib `time` module; safe via absolute imports but
  needless confusion to read. Dated/historical mentions of the old
  `backend/timeperiod.py` (the pre-2026-08-21 single-file version) left
  unchanged, same as every other renamed term on this page - not
  rewriting history, see [[08-technical-architecture]]'s Room->Faculty
  precedent.
  **Found, not touched:** a separate, pre-existing "Timeperiod" - the
  UI **Room** name (`docs/07-features.md`'s Rooms table has "Time
  periods"; `devtools/README.md`'s template listing and a comment in
  `temporal/phrase_matching.py` both say "Timeperiod", one word) is a
  different, product-facing concept from the code package just
  renamed, spelled two different ways already before today - worth its
  own naming conversation, not assumed to mean the same rename applies.
- `temporal/`'s three files renamed for the same reason as the package
  itself - short, generic nouns that didn't say what they held:
  `matchers.py` -> `phrase_matching.py`, `resolve.py` ->
  `duration_resolution.py`, `frozen.py` -> `frozen_duration.py`
  (`relative.py` -> `relative_time.py` too, same pass). All internal
  cross-imports between the four files, `temporal/__init__.py`'s
  re-exports, and every mention elsewhere (`storage.py`, `plan.py`,
  `outcome_classifier.py`, `devtools/app.py`, `README.md`, docs)
  updated to match; dated mentions of the original 2026-08-24 split
  (`docs/08-technical-architecture.md`'s "was split into a package
  (`matchers.py`/`resolve.py`/`frozen.py`)") left as historical record,
  same principle as every other rename today.

## 2026-08-24

- Board cleanup: 15 test/debris `goal_id`s (duplicate goals and dev-task
  goals from earlier testing sessions - "make dinner" x3, "make
  user_id", "fix active column," etc.) marked `completed=True` via
  `save_plan()`, the same mechanism the real "Goal complete" feedback
  path uses - not a raw JSON edit. Active board went from 22 to 7 real
  goals. `data/plans.json` is git-ignored, so this is the only durable
  record of the cleanup; history itself is untouched and append-only.
- Major `backend/` reorganization - `agent/{specialized,distributed}`,
  `world/` (empty placeholder), `devtools/` moved to a top-level
  sibling of `backend/`, `backend/devtools/view.py` removed as unused.
  See [[08-technical-architecture]] § Faculties for the full reasoning
  and vocabulary (Rooms/Faculties -> narrow/broad faculty, Cognition/
  Recognition/Acting, Infrastructure as a fourth category).
- `docs/14-semantic-time.md` drafted, expanding the "semantic
  understanding of time" idea in [[13-ideas-parking-lot]].
- `tools/docs_lint.py` added: checks docs/ and code comments for
  personal-narrative language (CONVENTIONS.md § Documentation
  neutrality) - two confidence tiers, same reasoning as
  `outcome_classifier.py`. Applied retroactively to fix several
  existing instances across [[07-features]], [[08-technical-architecture]],
  and [[12-decisions]].

## 2026-08-21

- Split `backend/` into paired data/logic modules, matching a mental
  model the user generalized themselves during this session: "every
  function you write can be seen as its own small agent" - a data
  table lives in one file, the logic that acts on it lives in a
  sibling file. `storage.py` (persistence) / `goal.py` (goal_id
  grouping - `get_board()`/`get_latest_for_goal()`/
  `get_history_for_goal()` moved out of `storage.py` to their own
  file, built on public `load_history()` rather than the private
  loader); `goal_to_plan.py` renamed `plan.py`; `outcome_classifier.py`
  (logic) / `outcome_phrases.py` (data); `timeperiod.py` (logic) /
  `timesegments.py` (data, reorganized into 5 labeled sections as it
  grew across the day - basic facts, calendar names, named
  segments/fractions, point-in-time recognition, duration/quantity
  recognition).
- Fixed a real drift bug in `replan()`: it only ever saw the
  immediately-previous plan, and `REPLAN_SYSTEM_PROMPT` said "make
  smaller" with no floor. Reproduced and confirmed: `right_now` shrank
  from "research 4 companies" to "check the news for 30 seconds" over
  13 simulated replans, never advancing toward "send an application".
  Fixed by passing `replan()` the full goal history (not just the
  previous plan) and adding an explicit prompt rule - only shrink the
  FIRST time, then move toward the core action.
- Replaced the fixed Yes/Still working on it/No/Goal complete buttons
  with a deterministic (no LLM) classifier over free-text feedback -
  `classify_outcome()` matches known phrases per outcome
  (`outcome_phrases.py`'s `RULES`), returns `None` for anything
  unrecognized (treated as a safe no-op "in_progress", never guessed
  toward "done"/"goal_done"). Word-boundary matching
  (`_contains_phrase()`) fixes a false-positive risk found while
  testing: naive substring matching made "no" match inside
  "not"/"know"/"now".
- Extensive new deterministic time-phrase recognition in
  `timesegments.py`/`timeperiod.py`, all hardcoded/no LLM, several bugs
  found and fixed via direct testing:
  - day-segment + day-offset combined - "tomorrow evening" had been
    resolving against *today's* date, silently ignoring "tomorrow"
  - week/month/year added to `PERIOD_PHRASES`, and `DURATION_LENGTH_RE`
    extended to week/month/year (previously only minute/hour/day, so
    "12 months" fell all the way through unrecognized)
  - month names ("in March") and weekday names ("next Monday", "this
    Friday", bare "Monday" with its own nearest-occurrence meaning)
  - literal clock times, 12h ("1 o'clock", "3pm") and 24h ("14:30",
    "00:00") - bare "o'clock" with no am/pm is a documented PM
    convention, not a guess
  - named fractions of an hour/minute/day ("half an hour", "quarter of
    a day"), reusing `HOUR_SEGMENTS`/`MINUTE_SEGMENTS`/`DAY_FRACTIONS`
  - deliberately narrow where a bare match would have silently stated a
    wrong answer instead of failing honestly: month-name matching
    requires "in" first after "I may go" was found silently
    "resolving" to next May (see [[11-experiments]]); bare 4-digit
    clock times ("1400") were considered and rejected (collides with
    prices/quantities, e.g. "1500kr"); `YEAR_FRACTIONS` was built,
    then removed after judging it didn't clear the same
    real-speech-pattern bar hour/minute/day fractions did (see
    [[12-decisions]])
- `SESSION-TODO.md` added (project root, not the docs/ vault) - a
  working scratch list for loose ends across a long single-day
  session, cleared as items get done or logged properly here / in
  [[11-experiments]].

## 2026-08-20 (latest x4)

- Added `tools/architecture_mapper/`: a standalone script (only uses
  Python's `ast` module on the target source, imports nothing from
  `backend`) that parses a package's modules/functions/imports into a
  dependency graph and renders it as drawio XML - a proper
  Sugiyama-style layered layout (longest-path layering from entry
  points, barycenter + transpose crossing minimization, a
  straightening pass), measured at zero edge crossings on this
  codebase. Deliberately kept outside `backend/` so it stays
  extractable as an external tool later (see [[12-decisions]]).
  Generated output is git-ignored - a regenerable build artifact, not
  tracked.

## 2026-08-20 (latest x3)

- Rebuilt `docs/08-architecture.drawio`'s NOW section at module/file
  level (mirrors `backend/README.md`'s table), fixing several real
  layout issues found via visual inspection along the way: arrows
  cutting through unrelated boxes, lateral edges overlapping text
  (fixed by docking at the exact top corner instead of box center), an
  entry-point pinning trade-off (0 crossings vs. one row of 4 - user
  chose the row of 4 explicitly when asked). VISION section unchanged
  in substance.
- Logged the `goal_id` identity decision and the
  `tools/architecture_mapper` decision (why build it now, why keep it
  outside `backend/`) in [[12-decisions]].

## 2026-08-20 (latest x2)

- Frontend: board/index layout is now N equal `.col` columns (was a
  fixed 2-column main/side layout) - `index.html` shows Set a goal |
  Active | Completed side by side, `board.html` shows Active |
  Completed side by side.
- New `_active_goal.html`: an active goal's full history renders as a
  You/Agent chat thread (a goal_id's chain of records already *is* one
  conversation - see `get_history_for_goal()`) instead of a flat
  key:value dump. Each card gets its own outcome form scoped to that
  specific goal_id. `_plan_entry.html` stays the plain data view, now
  only for Completed goals and the historical log.
- Found via real Chrome DevTools Protocol click-testing (not just
  server-side testing) that "Still working on it" appeared broken: the
  real cause was the page redirecting to the top instead of the
  specific goal's own anchor, burying the confirmation below the fold
  in a growing thread - not (as first suspected) an Enter-key bug.
  Fixed with `id="goal-{{ goal_id }}"` + a redirect to that anchor.

## 2026-08-20 (latest)

- Backend: `goal_id` is now a stable identity separate from a goal's
  display text (backfilled for legacy records so history's grouping
  doesn't shift) - fixes "take a shower"/"take shower" fragmenting into
  separate board entries just from retyping. `get_board()` groups by
  `goal_id`, not exact text match.
- New storage helpers `get_latest_for_goal()`/`get_history_for_goal()` -
  needed once more than one goal can be active at the same time.
- `/feedback` now scoped to the `goal_id` the form names, not "whatever
  was globally touched most recently" - with two+ active goals, that
  distinction is the difference between feedback landing on the goal
  you meant vs. a different one (a real bug, found via direct data
  inspection, not a hypothetical).
- New "in_progress" outcome ("Still working on it"): checks in without
  calling `replan()`, so a goal's plan can't drift/shrink just because
  time passed with no real success/failure signal - found via real
  usage: repeated "not done" clicks meant as "still working on it" had
  been shrinking a task 30min -> 15min -> 5min.

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
