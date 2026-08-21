# 13 — Ideas / Parking Lot

> Things we're not building now, but don't want to forget. See
> [[00-project-brief]] §11 ("What We Are NOT Going to Do Right Now").

- Multi-device sync via end-to-end encryption (log in on a new device,
  get the same agent/history back; server never sees plaintext) — see
  [[08-technical-architecture]] § Multi-device vision
- Calendar integration
- Push notifications / proactive outreach from the agent
- iOS app with Swift/SwiftUI (see [[08-technical-architecture]])
- Android / cross-platform (React Native, Flutter)
- Duolingo-style habit/identity mechanics (streaks, gamification)
- Low-friction interaction: voice, short text replies, one-button
  feedback, "agent only asks when necessary" (see [[00-project-brief]])
- Web interface translating the same portable data into a UI — timeline,
  goals, progress views (see [[08-technical-architecture]] § Long-term architecture)
- Aggregation / world-data capability the agent can call on (weather,
  calendar, maps, resources, user's own past activity) — a capability,
  not the core product, see [[08-technical-architecture]] § Long-term architecture
- Reflection / progress summaries ("you actually trained 1 hour/week —
  that's 52 hours this year")
- Folder-per-time-period storage + a "scanning" planning algorithm that
  walks the hierarchy (year/month/week/day as real files, not JSON
  fields) instead of a database — see [[08-technical-architecture]]
  § Memory & Data Architecture
- Let the free-text feedback note act as a real channel to the agent,
  not just status reporting: detect (deterministically, same approach
  as `backend/outcome_classifier.py` - no LLM guessing on *what kind*
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
  ([[12-decisions]]): without a real step list, nothing *structurally*
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
  approach as `backend/outcome_classifier.py` (no LLM guessing on
  *whether* a start time was named) if/when this gets built.
