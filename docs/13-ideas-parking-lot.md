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
  build, an addition to [[07-features]] § Knowledge once that room
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
  noted in the step-list drift fix above ([[12-decisions]]) and with
  the existing `duration`/`PLAN_KEYS` machinery ([[07-features]] §
  Time periods, `backend/agent/distributed/temporal/`). Directly what prompted the
  "Faculties" framing in [[08-technical-architecture]], same day -
  `backend/agent/distributed/temporal/` is that framing's first concrete example.
  Expanded into its own draft doc the same day - see [[14-semantic-time]].
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
  (not settled) in [[08-technical-architecture]]'s "Faculties" section,
  logged the same day - overlaps the ACTION node in that doc's
  long-term pipeline diagram, relationship not resolved.
