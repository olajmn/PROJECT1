# Session TODO — 2026-08-22/23

Working list of things we've noticed but haven't decided on/fixed yet,
so nothing gets lost while we figure out what to tackle first. Not
part of the docs/ vault (that's permanent project documentation) -
this is scratch, meant to be cleared once everything on it is done or
has been moved into a proper dev log/decision entry. See the previous
version of this file (now cleared, all items done) for the pattern.

## Open — noticed, not yet decided/fixed

- [x] **Horizons broader than the given duration still get filled in** -
      done 2026-08-23. `backend/timeperiod.py`'s new
      `broadest_relevant_horizon()` computes, from the resolved span's
      real length, which PLAN_KEYS horizon is the broadest one worth
      filling (coarse day-count thresholds - ~300d for one_year, ~25d
      for one_month, etc). `plan.py`'s new `_horizon_scope_instruction()`
      turns that into an explicit "fill these / leave these null" line
      appended to both `generate_plan()`'s and `replan()`'s prompts -
      the model is TOLD the boundary, not left to guess it (the
      original design) or told to ignore it (last night's change).
      Verified: "3 months" no longer gets a `one_year` entry. Known
      residual imperfection, not a bug in the logic: the model doesn't
      always fill in every horizon it WAS told to (e.g. left
      `this_minute` null once despite being told to fill it) - same
      class of instruction-following unreliability seen elsewhere
      tonight with this local 8B model.

- [ ] **Merge the goal + duration fields into one text box** - user
      wants "Set a goal" to be a single free-text field (button
      relabeled "Set goal"), typing goal and timing together
      ("clean the apartment this weekend") instead of two separate
      inputs - and if no timeframe is mentioned in what's typed, the
      agent should ask for one (deterministically, before even calling
      the model - same "code decides, model is just told" philosophy
      as the horizon-scope fix above). Investigated but NOT built
      tonight - real finding along the way: `_matched_day_segment()`
      and `_matched_period_phrase()` in `backend/timeperiod.py`
      currently use a naive substring check (`if word in lowered`),
      not word-boundary matching. That's safe today only because
      duration text lives in its own short, dedicated field - "this
      week" would falsely match inside "this weekend", "night" inside
      "midnight", the moment these matchers run against a full natural
      sentence instead. Same bug class as the already-fixed "may"/May
      month-name collision (docs/12-decisions.md) - needs the same
      word-boundary treatment BEFORE this feature is safe to build.
      Also needs a design answer for the "continue an existing goal"
      dropdown flow, which currently uses the separate duration field
      to let you set a NEW timeframe when continuing - no clear single-
      field equivalent decided yet. Raised 2026-08-23.

- [ ] **Vertical/hierarchical step list, not one flat list per goal** -
      user's concrete trigger: "improve my diet" over 3 months produces
      steps like "Sep 06-Sep 22 Make a list of healthy grocery items" -
      a single step spanning 16 days, because today's step_count()/
      MIN_STEPS/MAX_STEPS (backend/timeperiod.py) was tuned for
      single-session goals (a 20-minute goal breaking into ~15-minute
      steps), not multi-month ones, so a long goal's "steps" are really
      acting as coarse PHASES, not the granular actions they're meant
      to be. User's proposed shape: each step also carries its own
      smaller goal/horizon underneath it - closer to a real nested
      hierarchy (a `this_week` step has its own `today`-level sub-steps,
      etc) than today's one flat list stretched across the whole span.
      This is the SAME open question already sitting in
      docs/13-ideas-parking-lot.md under "Plan as an ordered step
      list" ("which horizons actually become step-lists... we take it
      bit by bit") - not a new idea, a real elaboration of that
      existing deferred one. Not designed or built - needs its own
      conversation given the size (touches step generation, the step
      list's own prerequisite-ordering problem one level deeper, and
      the UI). Raised 2026-08-23.

- [ ] **Should a goal auto-complete once every step is checked "Done?"?**
      Currently it doesn't - _active_goal.html just shows "All steps
      done - mark the whole goal complete below" once
      `current_step == len(steps)`, and the user still has to type
      something that `classify_outcome()` reads as `goal_done` (see
      app.py's /feedback) to actually mark it complete. This IS
      deliberate, not an oversight: finishing the step list only means
      "did what was planned for THIS timeframe" (e.g. one 20-minute
      session), not necessarily "the whole goal is achieved" - same
      reasoning the outcome classifier already follows everywhere else
      (never let the system guess something as consequential as
      goal-done; the user says so explicitly). Real tension worth its
      own conversation: auto-completing would probably be right for a
      one-shot goal ("make dinner") but wrong for an ongoing habit goal
      ("become a better reader") - not obviously a "just build it"
      change. Raised 2026-08-23.

- [ ] **Revisit visual design holistically, not one color at a time** -
      immediate trigger was disliking the purple `.model-label`/
      `.yaml-key` color (`#7c3aed` in style.css), but user explicitly
      wants to step back and look at the interface's whole visual
      language together rather than fix single colors in isolation.
      Raised 2026-08-23.

- [ ] **Clean up test-artifact active goals from tonight's session** -
      board currently has 16 active goals, several clearly test debris
      from building/testing tonight's features rather than real goals:
      `goal_id` 16/17 (duplicate "read a book"), 22/23/24 (duplicate
      "make dinner", from testing the timeperiod bar), 25/26/27 (from
      testing the clarifying-question flow - "read 20 pages...",
      "become a better reader", "improve my writing"). Not touched yet
      - user wants to review before marking complete/deleting.

## Done, just noting for the record (this session, 2026-08-22)

- Clarifying-question flow for vague goals (generate_plan() can ask
  instead of invent), plan horizons widened 4 -> 7, resolve_duration()
  made properly public, "Generating plan..." loading state, Knowledge
  (RAG) room sketched in docs (not built) - see git log, commits
  76b5c49/face2fa/d387422 on multi-goal-ui-and-goal-id.
