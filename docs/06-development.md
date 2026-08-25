# 06 — Development

> The original methodology, and what we've learned by building.
>
> Merged 2026-08-25 from the original `04-hypothesis.md` + `10-development.md`
> + `11-experiments.md` + `13-ideas-parking-lot.md`; "The Approach"
> (Phase 1-9) moved in from [[00-project-brief]] the same day - it's
> process/methodology, not identity. Content is unchanged from the
> source files except cross-references to renamed docs; dated entries
> otherwise describe the project as it was on that date, including old
> code paths (same convention this vault already followed for itself -
> see `../COLLABORATION.md` § Meta-coherence).
>
> The sections below map to this file's status vocabulary:
> **§ Hypothesis** = HYPOTHESIS, **§ Development Log** = a running FINDING/
> build record, **§ Experiments** = EXPERIMENT (with a FINDING each),
> **§ Parking Lot** = PARKED. OPEN and REJECTED are used inline, within
> entries, wherever a specific question or option is called out as such -
> not retrofitted as a per-line tag across the whole log in this pass.

## 1. The Approach

> Moved from [[00-project-brief]] 2026-08-25 - the original planning
> methodology (2026-08-18), kept here as the record of how the project
> was actually approached, not as current identity. Every "Phase N"
> reference elsewhere in this vault points here.

Here's how I'd set up the project:

### Phase 1 — Problem

Define, very concretely:

> What problem are we solving?

### Phase 2 — Research

Investigate existing solutions.

Map out:

- competitors
- features
- user experience
- weaknesses
- reviews
- what users are actually asking for

### Phase 3 — Hypothesis

Formulate:

> "We believe that ..."

Example:

> "We believe that people don't primarily need help creating plans, but help continuously translating plans into concrete actions."

### Phase 4 — Product Definition

Decide:

- who the first user is
- what problem the MVP solves
- what the agent does
- what the agent does NOT do
- what the user does
- what the "minimum useful product" is

### Phase 5 — User Flow

Map out the whole journey:

```
New user
↓
States a goal
↓
Agent asks questions
↓
Agent creates a plan
↓
User approves
↓
Today's action
↓
Feedback
↓
Agent evaluates
↓
Next action
↓
Replanning
```

### Phase 6 — Technical Design

Now we start figuring out:

- frontend
- backend
- database
- LLM API
- agent architecture
- authentication
- scheduling
- notifications
- memory
- APIs/tools

### Phase 7 — MVP

Build the smallest version that actually demonstrates the idea.

Don't build everything.

### Phase 8 — Testing

Let real people use it.

Look especially for:

> "What does the agent do that actually helps?"

and:

> "When does the agent just become annoying?"

### Phase 9 — Iteration

Keep building based on actual usage.

### See also

- [[00-project-brief]]
- § Hypothesis below

## 2. Hypothesis

> Phase 3 above.

### Template

> "We believe that ..."

### Current hypothesis (draft from the kickoff conversation)

> We believe that people don't primarily need help creating plans, but
> help continuously translating plans into concrete actions.

And more specifically (the question the project should investigate):

> Can we build an agent that means the user needs to spend significantly
> less mental energy planning, prioritizing, and organizing the path from
> goal to actual action?

### Refined framing (from a parallel ChatGPT discussion, 2026-08-18)

The project is a **personal agent**, not a planning app. Planning is one
capability the agent uses, not the product itself. The hypothesis is
really about a continuous loop, not a one-time plan:

```
GOAL → PLAN → TODAY/RIGHT NOW → ACTION → USER FEEDBACK → REPLAN → ACTION → MEMORY ↺
```

**"Prototype 0.1"** = the smallest version of this loop that actually
closes the circle back into a new action:

```
User gives goal → Agent creates plan → Agent gives concrete action →
User performs / doesn't perform it → User gives feedback → Agent
interprets feedback → Agent changes the plan → Agent gives next action
```

This reframes what's actually being tested: not "can an LLM make a
plan" (trivial, already proven) but **"does closing this feedback loop
create real value for the user."** See [[02-product]] § MVP for build status.

### How we test it

Real usage by the project owner, logged as it happens - see
§ Experiments below for individual test entries and the Status section
directly below for where that testing currently stands.

### Status

- [ ] Not tested yet
- [x] Partially supported
- [ ] Disproven — see why below

**As of 2026-08-19:** Real usage happened for the first time (multiple
goals, multiple feedback rounds, in one evening rather than spread
across days). Mixed signal:

- The core loop mechanism (goal → plan → right_now → feedback → replan
  → new right_now) holds up over short chains (1-3 rounds) - verified
  across dozens of real records.
- Two real failure modes emerged that limit trust: severe hallucination
  on non-English input, and drift over long replan chains (8+ rounds) -
  see § Experiments entries this date.
- Whether the loop is actually *useful* (the real hypothesis question)
  is still not answered - tonight's testing was compressed into one
  session and skewed toward stress-testing failure modes, not the
  sustained, paced, multi-day use the hypothesis actually needs to be
  judged against.

### See also

- [[01-research]] § The Problem
- [[01-research]] — informs the hypothesis
- [[02-product]] — the hypothesis drives the product definition

## 3. Development Log

> § The Approach above, Phase 7-9. Running log, newest first.

### 1. 2026-08-25 (latest)

- Later the same day, `backend/` was reorganized again: `agent/
  {specialized,distributed}` (see the 2026-08-24 entry below) was
  replaced by topic-based folders - `foundation/` (time/, plus empty
  scaffolds language/, memory/, meaning(maybe)/), `goals/`, `planning/`,
  `infrastructure/`, `world/`. Goal and Planning became Domains/Rooms
  as direct siblings, not nested under an `agent/` wrapper - `agent/`
  was removed entirely. See [[03-architecture]] for the resulting
  structure, [[04-current-state]] for what's built vs. scaffold within
  it.
- Picked "Semantic understanding of time" off `../SESSION-TODO.md`'s
  five-item list (the other four stay parked). Built the first,
  narrower half of the idea in [[03-architecture]] § Time:
  `relative_length()`
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
  [[03-architecture]] § Time.
  Not yet wired into any caller (`plan.py`,
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
  (`docs/03-architecture.md`'s "Temporal awareness -> the
  Time faculty" mapping, "Temporal grounding" in this log's 2026-08-19
  entry) - removes the recurring "Time (`timeperiod/`)" translation
  every doc mention needed. `time/` was considered and rejected -
  shadows Python's stdlib `time` module; safe via absolute imports but
  needless confusion to read. Dated/historical mentions of the old
  `backend/timeperiod.py` (the pre-2026-08-21 single-file version) left
  unchanged, same as every other renamed term on this page - not
  rewriting history, see [[03-architecture]]'s Room->Faculty
  precedent.
  **Found, not touched:** a separate, pre-existing "Timeperiod" - the
  UI **Room** name ([[03-architecture]] § System structure's
  Domains table has "Time periods"; `devtools/README.md`'s template listing and a comment in
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
  (`docs/03-architecture.md`'s "was split into a package
  (`matchers.py`/`resolve.py`/`frozen.py`)") left as historical record,
  same principle as every other rename today.

### 2. 2026-08-24

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
  See [[03-architecture]] § Faculties for the full reasoning
  and vocabulary (Rooms/Faculties -> narrow/broad faculty, Cognition/
  Recognition/Acting, Infrastructure as a fourth category).
- `docs/14-semantic-time.md` drafted, expanding the "semantic
  understanding of time" idea in § Parking Lot below. (Merged into
  [[03-architecture]] § Time, 2026-08-25.)
- `tools/docs_lint.py` added: checks docs/ and code comments for
  personal-narrative language (CONVENTIONS.md § Documentation
  neutrality) - two confidence tiers, same reasoning as
  `outcome_classifier.py`. Applied retroactively to fix several
  existing instances across [[02-product]] § Capabilities, [[03-architecture]],
  and [[05-decisions]].

### 3. 2026-08-21

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
    "resolving" to next May (see § Experiments below); bare 4-digit
    clock times ("1400") were considered and rejected (collides with
    prices/quantities, e.g. "1500kr"); `YEAR_FRACTIONS` was built,
    then removed after judging it didn't clear the same
    real-speech-pattern bar hour/minute/day fractions did (see
    [[05-decisions]])
- `SESSION-TODO.md` added (project root, not the docs/ vault) - a
  working scratch list for loose ends across a long single-day
  session, cleared as items get done or logged properly here / in
  § Experiments below.

### 4. 2026-08-20 (latest x4)

- Added `tools/architecture_mapper/`: a standalone script (only uses
  Python's `ast` module on the target source, imports nothing from
  `backend`) that parses a package's modules/functions/imports into a
  dependency graph and renders it as drawio XML - a proper
  Sugiyama-style layered layout (longest-path layering from entry
  points, barycenter + transpose crossing minimization, a
  straightening pass), measured at zero edge crossings on this
  codebase. Deliberately kept outside `backend/` so it stays
  extractable as an external tool later (see [[05-decisions]]).
  Generated output is git-ignored - a regenerable build artifact, not
  tracked.

### 5. 2026-08-20 (latest x3)

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
  outside `backend/`) in [[05-decisions]].

### 6. 2026-08-20 (latest x2)

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

### 7. 2026-08-20 (latest)

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

### 8. 2026-08-19 (latest x2)

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

### 9. 2026-08-19 (latest)

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
  answers. See § Experiments below and [[05-decisions]] for the
  write-goals-in-English decision this led to.
- Board cleanup: all 7 pre-existing active goals marked complete (new
  records, nothing deleted - 32 history entries intact) to give a clean
  "Active" board before starting real usage testing.

### 10. 2026-08-19

- Temporal grounding: `goal_to_plan.py` now sends the real current
  date/time (`_now_str()`) to the model on every `generate_plan()` and
  `replan()` call, so "right now" is grounded in the actual moment
  instead of the model having no sense of time. First concrete step
  toward the still-unbuilt "Temporal awareness" item in
  [[03-architecture]].
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
  readability, not product polish, see [[05-decisions]].
- Logged a user-proposed idea (folder-per-time-period storage + a
  scanning planning algorithm over it) into
  [[03-architecture]] § Memory and
  § Parking Lot below — not built, matches the existing
  "testing over further ideation" decision in [[05-decisions]].

### 11. 2026-08-18 (latest x5)

- Cleanup pass via `/code-review` + `/simplify` on `backend/` (5 parallel
  agents: correctness, reuse, simplification, efficiency, altitude —
  see [[05-decisions]] for the full list of what was fixed vs. skipped).
  Highlights: `storage.py` now owns the plan schema (`PLAN_KEYS`) and
  normalizes legacy string-format plans once, at the source, instead of
  every reader special-casing them; atomic writes to `plans.json`;
  `view.py`'s hand-built HTML replaced with a proper Jinja template
  (`history.html`), fixing an HTML-escaping gap the templated `index.html`
  didn't have; Flask routes no longer crash on missing form fields or an
  empty history. Tested: `today.py`, `view.py`, and `app.py` (including
  the fixed edge cases and the XSS-escaping fix) all re-verified working.

### 12. 2026-08-18 (latest x4)

- Initialized git, verified `.gitignore` correctly excludes `data/`
  (personal goals/plans), `.venv/`, `__pycache__/`, `.DS_Store` before
  first commit. Created private GitHub repo
  ([github.com/olajmn/personal-ai-agent](https://github.com/olajmn/personal-ai-agent))
  and pushed initial commit (Prototype 0.1, full loop closed).

### 13. 2026-08-18 (latest, latest, latest)

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

### 14. 2026-08-18 (latest, latest)

- Built `backend/app.py`: local interactive web page (Flask) — set a
  goal, see "right now", give feedback via buttons/text. Closes
  Prototype 0.1's full loop (see [[02-product]] § MVP, § Hypothesis above)
- Added `replan()` to `goal_to_plan.py`: takes the previous plan + user
  feedback, asks the LLM for an updated plan
- Extended `storage.save_plan()` with an optional `feedback` field
- Installed Flask into `.venv/` (was floating in system Python before —
  now properly isolated per `../CONVENTIONS.md`)
- Tested end-to-end via curl: goal → plan → feedback ("too busy today")
  → replan produced a smaller, easier next action, as intended

### 15. 2026-08-18 (latest)

- Integrated a parallel ChatGPT discussion into the vault: refined
  hypothesis as a closed loop ("Prototype 0.1"), added temporal
  awareness + memory/data architecture ideas to [[03-architecture]],
  added new parking-lot items (voice, web UI, aggregation, reflection),
  logged two decisions in [[05-decisions]] (agent-not-planner-app reframe,
  testing over further ideation). No code changed in this pass.

### 16. 2026-08-18 (even even later)

- Reorganized: all Python code moved into `backend/` (a "src layout" -
  root now holds only folders + standard project metadata files like
  `.gitignore`/`requirements.txt`, which stay at root because Git/pip
  expect them there). Added `backend/README.md`. Fixed `storage.py`'s
  data path for the new nesting level. Verified no data lost.

### 17. 2026-08-18 (even later)

- Switched `goal_to_plan.py` to structured JSON output (`format="json"`
  in Ollama) instead of free text — keys: `one_year`, `one_month`,
  `this_week`, `right_now`
- Added `today.py`: prints just `right_now` from the latest saved plan —
  the "zoom all the way in" step from [[00-project-brief]] §2

### 18. 2026-08-18 (later)

- Added `storage.py`: goal+plan history persisted to `data/plans.json`
  (append-only, not overwritten). See [[05-decisions]] for why history
  over overwrite, and the privacy trade-off of unencrypted local JSON.
- Added `data/` to `.gitignore` — personal goals/plans must never be
  committed
- Added `docs/08-architecture.drawio` — full visual architecture diagram

### 19. 2026-08-18

- Set up `goal_to_plan.py` (v0.1): goal → plan via LLM, no storage yet
- Tried Anthropic Claude (`claude-opus-5`) first — invalid API key (401)
- Switched to a local LLM via **Ollama** (`llama3.1:8b`) — no key, no
  cost, runs on the local machine. See [[05-decisions]]
- Cleaned up the Python environment: created `.venv/` to avoid conflicts
  between two Python 3.14 installations on the machine
- Set a code convention: all code and docs in English, see `../CONVENTIONS.md`
- Set up the `docs/` folder as an Obsidian vault, originally sketched as
  13 numbered files: 01 Problem, 02 Research, 03 Competitors, 04
  Hypothesis, 05 Product, 06 User flows, 07 Features, 08 Technical
  architecture, 09 MVP, 10 Development, 11 Experiments, 12 Decisions, 13
  Ideas/Parking lot. Restructured 2026-08-25 into the current `00`-`06`
  plus `../COLLABORATION.md` (see [[04-current-state]] for why and the
  mapping) - kept here as the historical record of the original plan,
  not the current layout.

### See also

- [[02-product]] § MVP
- § Experiments below

## 4. Experiments

> Tests of § Hypothesis above and product assumptions.

### Template

**Hypothesis tested:**
**Setup:** (who, how many, how)
**Result:**
**Learning:**
**Consequence:** (what do we change based on this?)

### Log

#### 1. 2026-08-21 — Naive substring matching in the free-text outcome classifier gives false positives

**Hypothesis tested:** N/A - found while building `backend/outcome_classifier.py`,
before it shipped, not from a designed test.
**Setup:** Tried the initial (plain substring) phrase matcher directly against
realistic edge-case free text before wiring it into the UI - e.g. "I don't
know yet", "not right now".
**Result:** A naive `if phrase in text` check for the recognized word "no"
matched *inside* "not", "know", "now" - "I don't know yet" would be
classified toward a negative outcome purely because "no" appears as a
substring of "know", even though the sentence never actually says no.
**Learning:** The exact same shape of risk as two later findings the
same day: "I may go" nearly resolving to next May (`_matched_month_name()`),
and the reason `DEADLINE_RE` needed a tolerant regex instead of an exact
phrase list. Any short recognized word that's also a substring of a
common longer word breaks under plain text containment - a systematic
risk in this project's whole "recognize known phrases" approach, not a
one-off bug.
**Consequence:** Fixed before shipping, via word-boundary regex matching
(`_contains_phrase()`, `\b`-wrapped so a phrase only matches as a whole
word) - see [[05-decisions]]. Same fix shape reused later the same day
for month-name matching (requiring "in" before the month name). General
principle going forward: never trust substring containment alone for a
short recognized word.

#### 2. 2026-08-20 (latest) — Long replan chains drift toward trivial actions, confirmed under real (non-stress-test) usage

**Hypothesis tested:** Does the 2026-08-19 stress-test finding below (drift
under 8 rapid clicks in under a minute) also show up under genuinely paced
real usage - actual attempts and feedback spread over hours, not a
deliberate rapid-fire test?
**Setup:** Real usage, goal "send 4 work applications" (`goal_id` 11),
spanning 2026-08-19 19:49 to 2026-08-20 19:00 - 15 total replan rounds
over roughly a full day of ordinary (not deliberately adversarial)
interaction.
**Result:** `right_now` degraded steadily across the chain: "Research and
list 4 job openings that match my skills and experience" → "List 4 job
openings... from companies already researched" → "research one company
for 30 minutes" → "browse a single job opening website" for 15, then 5,
then 2 minutes → "Spend 30 seconds checking the news for a new job
opening" - the action in the LAST of all 15 records. Across the entire
chain, `right_now` never once mentioned actually sending an
application - the goal's own stated action.
**Learning:** Confirms the 2026-08-19 stress-test finding wasn't an
artifact of rapid-fire clicking - the identical degradation happens
under genuinely paced real usage too, just slower. `replan()` only ever
saw the immediately-previous plan, so each individual shrink looked
locally reasonable to the model in isolation, but nothing stopped the
chain from compounding indefinitely further away from the goal itself.
**Consequence:** Fixed 2026-08-21 (see [[05-decisions]]): `replan()` now
receives the goal's FULL history (every right_now + feedback pair,
oldest first) instead of just the previous plan, and
`REPLAN_SYSTEM_PROMPT` now explicitly says to only shrink `right_now`
the first time it isn't completed, then move toward the goal's actual
core action instead of shrinking again. Verified against a simulated
reproduction of this exact 13-replan chain after the fix - `right_now`
advanced toward sending an application instead of continuing to shrink.

#### 3. 2026-08-20 — Hallucinated a specific person ("a friend") never mentioned

**Hypothesis tested:** N/A - noticed during real usage, not a designed test.
**Setup:** Real usage, goal "start going to the gym" (`goal_id` 12), no
duration given. First plan's `right_now`: "Research and shortlist 3 gyms
in the area and make a list of their membership options and pricing."
User feedback: "did not complete the action" plus a note about timing -
no other person mentioned anywhere.
**Result:** The next `right_now` read "Schedule a short call with a
friend to ask for their gym recommendations" - inventing a specific
person ("a friend") the user never mentioned in the goal text or the
feedback.
**Learning:** Same category as the earlier "chapter 11" (2026-08-18) and
"German vocabulary" (2026-08-19) hallucinations - a small, plausible-
sounding, entirely fabricated specific, not an obviously-wrong answer,
which is exactly what makes this kind of failure risky: it reads as
reasonable advice unless you notice you never actually said that.
**Consequence:** No fix applied (same as the other hallucination
findings - see [[02-product]] § MVP, Important distinction). Logged as further
evidence of an already-known limitation, not a new one. Reinforces this
project's core distinction between "the mechanism working" (plan → save
→ display → replan all functioned correctly here) and "the output being
reliable" (the specific content wasn't grounded in anything the user
actually said).

#### 4. 2026-08-19 — Long replan chains drift away from the original goal

**Hypothesis tested:** Does the replan loop stay anchored to the original
goal over many consecutive "not done" cycles, or does it drift?
**Setup:** Real usage by the project owner via `backend/devtools/app.py`.
Goal: "take a shower" (duration "1 hour"). Pressed "No" 8 times in a
row, in rapid succession (well under a minute total - a stress test,
not paced real-world usage), then "Yes" twice with a corrective note.
**Result:** The `right_now` action drifted steadily away from showering:
"go to the shower area" → "get the shower cleaner" → "find the remote
control to turn on the bathroom light" → "get out of bed" → "get
dressed" → "put on socks" → `null`. The user had to type "no i'm gonna
take a shower" to redirect it; even then the final response returned
`right_now: null`.
**Learning:** Not an isolated hallucination (like the earlier "chapter
11" or "German vocabulary" findings) - systematic drift over repeated
replan() calls. Confirms a known, previously-flagged architecture gap:
`replan()` only receives the immediately-previous plan, not the full
history or a reinforced original goal, so small deviations compound
over iterations. **Important caveat, discussed with the assistant
afterward:** 8 rapid "No" clicks with no real attempt in between is a
stress test, not representative of normal use (try the action for
real, then give feedback, likely once a day) - severity under normal
pacing is untested. The "Goal complete" button (built earlier the same
day) is an available escape hatch once a chain drifts.
**Consequence:** Logged as a known limitation of long replan chains
specifically, not of the core loop itself (which held up fine over 1-3
rounds throughout the rest of tonight's testing). Consider, before
further building: reinforcing the original goal text more strongly on
every replan() call, not just the previous plan. Revisit after testing
under normal (non-stress-test) pacing over several real days.

#### 5. 2026-08-19 — Goal identity is exact-text matching, not semantic

**Hypothesis tested:** N/A - incidental finding while building the
board feature (§ Development Log above).
**Setup:** Real usage: goal typed as "take shower" in one session, "take
a shower" (one extra word) in a later session, same real intent.
**Result:** `storage.get_board()` groups records by exact `goal` string
match - the two counted as two separate goals on the board, not one
continuing goal.
**Learning:** There is currently no concept of "this is the same goal"
beyond byte-for-byte text equality. A minor wording change (which
happens naturally in real use) fragments what should be one continuous
thread.
**Consequence:** Not fixed yet - noted as a real limitation. Fixing it
well (fuzzy/semantic matching, or an explicit goal ID the user
confirms) is more than a one-line change; revisit if it causes real
confusion during multi-day testing, rather than fixing preemptively.

#### 6. 2026-08-19 — Norwegian goal text causes severe, reproducible hallucination

**Hypothesis tested:** Does `llama3.1:8b` handle a goal written in Norwegian
as reliably as one written in English?
**Setup:** `generate_plan()` called directly (bypassing the UI) with the
same goal in both languages: `"lage mat"` (Norwegian for "make food") +
duration `"i løpet av kvelden"` ("during the evening") vs. the English
originals directly: `"make food"` + duration `"during the evening"`.
Repeated 3 times for the Norwegian phrasing to check reproducibility.
**Result:** All 3 Norwegian calls produced answers unrelated to cooking -
two of them invented "German" content from nowhere ("Learn 10 new German
vocabulary words", "German dishes... start with Spätzle"), one
suggested "Translate 'lage mat'..." instead of an actual action. The
English phrasing of the *identical* goal, on the same call, produced a
sensible, grounded answer ("Check what ingredients are available in the
pantry and fridge"). Confirmed unrelated to the duration-resolution
feature built earlier the same day - `resolve_duration()` (renamed from
`_resolve_duration()` 2026-08-22) correctly computed "kveld" (Norwegian
for "evening") → 17:00-23:00 in every case regardless of the plan
quality.
**Learning:** This is a more severe reliability failure than the
"chapter 11" hallucination (2026-08-18 below) - there, one detail was
invented; here, the *entire* response was disconnected from the actual
goal, consistently, only when the input was Norwegian. `llama3.1:8b`'s
multilingual handling appears to be a real, reproducible weak point,
not an occasional fluke.
**Consequence:** User decision: write goals in English going forward
(see [[05-decisions]]) rather than switch LLM backend yet - keeps
testing free/local while sidestepping the specific failure mode found.
Revisit the Ollama-vs-Claude decision if English-only turns out to be
too much friction, or if similar failures show up in English too.

#### 7. 2026-08-18 — First live use: hallucinated detail

**Hypothesis tested:** Does `llama3.1:8b` (local Ollama) give reliable,
grounded replanning answers, not just structurally valid JSON?
**Setup:** Real usage by the project owner via `backend/devtools/app.py`.
Goal: "Read one book this month." After 2 feedback rounds (not done →
smaller step; done → next step), the agent's "right_now" action referred
to "chapter 11" of a specific book.
**Result:** Fabricated detail. The user never stated a book title, a
chapter, or any reading progress. The model invented a plausible-sounding
but ungrounded specific fact.
**Learning:** The mechanism (LLM call → save → display → replan) worked
perfectly — this is a **content reliability** failure, not an engineering
failure. Confirms the risk flagged when `llama3.1:8b` was chosen over
Claude (see [[05-decisions]]): smaller local models hallucinate more,
especially when asked to "sound concrete." An execution agent stating
false specifics with confidence could actively mislead the user, which
is worse than being vague.
**Consequence:** No fix applied yet — logged as a known limitation (see
[[02-product]] § MVP, Important distinction). Decided not to switch to Claude
right now to avoid cost during free/exploratory testing (see
`../CONVENTIONS.md` and the user's cost-sensitivity preference). Revisit
if hallucinations happen often enough to undermine trust in testing, or
before any real (non-owner) user tests the agent.

### See also

- § Hypothesis above
- [[05-decisions]]

## 5. Parking Lot

> Things we're not building now, but don't want to forget. See
> [[02-product]] § Non-goals.

- Multi-device sync via end-to-end encryption (log in on a new device,
  get the same agent/history back; server never sees plaintext) — see
  [[03-architecture]] § Architectural principles
- Calendar integration
- Push notifications / proactive outreach from the agent
- iOS app with Swift/SwiftUI (see [[03-architecture]])
- Android / cross-platform (React Native, Flutter)
- Duolingo-style habit/identity mechanics (streaks, gamification)
- Low-friction interaction: voice, short text replies, one-button
  feedback, "agent only asks when necessary" (see [[00-project-brief]])
- Web interface translating the same portable data into a UI — timeline,
  goals, progress views (see [[03-architecture]] § Long-term architecture)
- Aggregation / world-data capability the agent can call on (weather,
  calendar, maps, resources, user's own past activity) — a capability,
  not the core product, see [[03-architecture]] § Long-term architecture
- Reflection / progress summaries ("you actually trained 1 hour/week —
  that's 52 hours this year")
- Folder-per-time-period storage + a "scanning" planning algorithm that
  walks the hierarchy (year/month/week/day as real files, not JSON
  fields) instead of a database — see [[03-architecture]]
  § Memory
- Let the free-text feedback note act as a real channel to the agent,
  not just status reporting: detect (deterministically, same approach
  as `backend/agent/specialized/outcome_classifier.py` - no LLM guessing on *what kind*
  of message it is) when a note reads as a question/request rather
  than a done/not-done/in-progress/goal-complete report, and route it
  through `replan()` as labeled feedback (e.g. "Asked: ...") so the
  agent actually responds instead of silently logging it as an
  unrecognized check-in. Found via real use, 2026-08-20: notes like
  "can you help me" / "maybe do some research for me" currently just
  get logged and ignored. Explicit caveat to carry into the eventual
  build: the agent still has no tools/internet access (see "Aggregation
  / world-data capability" above), so a "response" is bounded by the
  model's own training, not real live research.
- **Plan as an ordered step list, with "Task (right now)" as just the
  current step in it** — instead of today's model, where `right_now`
  is its own independently-generated text field with no real
  connection to a "step 2" waiting after it. Discussed 2026-08-21,
  directly motivated by the drift bug fixed the same day
  ([[05-decisions]]): without a real step list, nothing *structurally*
  stopped `right_now` from drifting into something meaningless -
  fixing it needed a promise in the prompt ("only shrink once"), not
  something the data shape itself prevented. A real step list (step 3
  of 7, inspectable) would make that kind of drift harder to produce
  in the first place.
  - Decided so far: the whole list is generated in one go, not built
    incrementally step-by-step - but flagged as still needing its own
    conversation, because a full `one_year` step list could get very
    long.
  - Explicitly deferred: which horizons actually become step-lists
    (`this_week` only, or `one_month`/`one_year` too) - "we take it
    bit by bit, but it's something to come back to."
  - Concept for when feedback changes direction: start simple - it
    changes which step it's currently asking about (edits/swaps the
    current step), not a full regeneration of the whole list. Real,
    named, unsolved problem this runs into immediately: steps have
    implicit prerequisites ("you can't put water in the kettle before
    you've gotten off the couch") - freely editing one step in
    isolation can silently break the steps that assumed it. Explicitly
    parked, not solved, at the concept stage.
  - Raised 2026-08-23: click into any individual step and generate
    steps FOR that step - the same "break this into smaller pieces"
    mechanism `_generate_steps()` already applies once to `right_now`,
    applied recursively/on-demand to any step in the list, drilling
    down as deep as needed. Same unsolved prerequisite problem as
    above applies one level deeper too (sub-steps inherit whatever
    their parent step assumed) - not a separate problem, the same one,
    just recursive.
- **Recognize a real, already-happened start time in what the user
  types** (e.g. "I started yesterday") and pass it to the model as
  context, distinct from `duration` (how far the plan should span
  *forward*) and from `PLAN_KEYS` (the plan's own forward-looking
  horizons, year down to right_now) - neither currently captures "this
  didn't start from zero just now." Discussed 2026-08-21, while
  expanding `PLAN_KEYS` to `today`/`this_hour`/`this_minute`: a real,
  if uncommon, case - flagged as its own mechanism (recognition +
  context passed to the model), not an extra `PLAN_KEYS` entry, since
  it answers "when did this actually begin" rather than "how does the
  plan look at this time window." Likely the same deterministic-phrase
  approach as `backend/agent/specialized/outcome_classifier.py` (no LLM guessing on
  *whether* a start time was named) if/when this gets built.
- **Export/share a goal's plan as a document** - let the user send or
  print a goal's plan (and maybe its full conversation history) as an
  actual document/file, not just something viewed live in the devtools
  UI. Raised 2026-08-23, explicitly flagged by the user as "for later"
  while working on the horizon-scale diagram in
  `active/_timeperiod.html` - not scoped or designed at all yet
  (format, what's included, whether it's a real feature or just a
  personal debugging convenience - in the spirit of the static-snapshot
  tool that used to live at `backend/devtools/view.py`, removed
  2026-08-24 once it turned out to be unused, see `backend/README.md`).
- **Fact-checking as a separate layer on top of the future Knowledge/
  RAG room, plus a three-way split of knowledge types.** Discussed
  2026-08-24 (from a ChatGPT summary the user brought in) - not a new
  build, an addition to [[03-architecture]] § Knowledge once that room
  gets built:
  - RAG and fact-checking are different things. RAG (retrieval) finds
    the stored chunks closest to a claim/question. Fact-checking is
    one function *built on top of* that retrieved material - it hands
    the claim and the sources to the model and asks for a verdict
    (e.g. "supported" / "mixed evidence" / "not supported" / "unknown")
    with the sources shown back to the user, instead of the model
    answering from training alone as if it knows for sure.
  - Pairs with keeping three kinds of knowledge distinct rather than
    blended in a response: personal (the user's own notes, experience,
    history, stated preferences), external (papers, documentation,
    other verifiable sources), and system data (dates, goals, actions,
    actual stored history - what the system already knows for
    certain). Same shape as the principle already followed elsewhere
    in the project for time understanding, goal identity, and step
    counting: don't let the model guess or invent what deterministic
    code or a real source can already establish.
  - Suggested build order once any of this becomes real: Goal → Plan →
    Feedback → History → Knowledge/RAG → Fact-checking. Fact-checking
    is meant to land as one function using the Knowledge layer, not a
    separate system built from scratch.
- **Semantic understanding of time, not just numeric duration.**
  Discussed 2026-08-24: the agent should understand what a duration
  actually means in context, not just convert it (1 hour = 60
  minutes). One hour of reading is a lot; one hour of training is
  comparatively little. The same hour is also relative - long next to
  15 minutes, short next to a full day. Consequence for planning: if
  the user only has 45 minutes available, the agent shouldn't
  automatically shrink whatever plan already exists - it may need to
  choose a different activity or plan entirely, not a shorter version
  of the current one. Overlaps with the "only shrink once" constraint
  noted in the step-list drift fix above ([[05-decisions]]) and with
  the existing `duration`/`PLAN_KEYS` machinery ([[03-architecture]] §
  System structure, `backend/agent/distributed/temporal/`). Directly what prompted the
  "Faculties" framing in [[03-architecture]], same day -
  `backend/agent/distributed/temporal/` is that framing's first concrete example.
  Expanded into its own draft doc the same day - see [[03-architecture]]
  § Time for what's built; open design questions as of 2026-08-25:
  - Where "what this duration means" comes from: RESOLVED for the
    relative-duration half - deterministic, hardcoded thresholds
    (`_RELATIVE_LENGTH_THRESHOLDS`), the "code decides, model is just
    told" principle ([[05-decisions]], 2026-08-20) applying here too.
    STILL OPEN for the activity-specific half: lookup table vs.
    model-informed reasoning, not decided.
  - Whether this belongs to the Time faculty or a different one:
    RESOLVED for relative-duration (pure magnitude comparison needs no
    knowledge of activities, fits Time cleanly). STILL OPEN for the
    activity-specific half - looks like it belongs to a Language/
    Semantics faculty that doesn't exist yet.
  - What "relative" duration requires: RESOLVED - a second duration
    string to compare against (`reference` in
    `relative_length(duration, reference)`). Nothing calls it with a
    real reference yet.
  - The actual trigger: STILL OPEN - `relative_length()` exists as a
    capability, isn't wired into `plan.py`/`replan()`/the UI anywhere
    yet, so whether it runs on every plan generation or only on shrink
    is undecided.
- **The agent actually doing things, not just explaining how.**
  Discussed 2026-08-24: distinguishes an agent that tells the user how
  to do something from one that produces the finished result itself.
  Concrete example raised: an app that generates Excel files, Word
  documents, text notes, or recipes, and uploads them to Google Drive.
  The specific file formats aren't the point - the point is going from
  a stated intention to an actual completed artifact. Flagged as close
  to the core definition of "agent" in this project (see
  [[00-project-brief]] - "Does the system make its own decisions?").
  This is the output/action counterpart to the already-parked
  "Aggregation / world-data capability" idea above, which is about the
  agent pulling information in. One of the candidate "faculties" named
  (not settled) in [[03-architecture]]'s "Faculties" section,
  logged the same day - overlaps the ACTION node in that doc's
  long-term pipeline diagram, relationship not resolved.
