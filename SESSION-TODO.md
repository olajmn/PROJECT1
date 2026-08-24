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

- [x] **Merge the goal + duration fields into one text box** - done
      2026-08-23, commit 5f2cf0a. `extract_duration_phrase()`
      (backend/timeperiod.py) searches the whole sentence for a
      recognized time phrase; the word-boundary prerequisite fix
      landed in the same commit. "Continue an existing goal" now
      repurposes the same field as an optional new-duration input
      (superseded again 2026-08-23 night by the conversational
      duration-change flow, commit 4396847 - the dropdown/"Extend
      timeframe" form is gone entirely).

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

- [x] **Clean up test-artifact active goals from tonight's session** -
      done 2026-08-24. Board had grown to 22 active goals by the time
      this was tackled (more test debris accumulated after this note
      was first written: Norwegian/rapid-fire test goals 18/19/20/21,
      and dev-task goals 29/32/33 - "learn backend development"
      duplicating the seed record, "make user_id" and "fix active
      column" literally naming dev tasks rather than personal goals).
      15 goal_ids marked `completed=True` via `save_plan()` (same
      mechanism the "Goal complete" feedback path already uses, not a
      raw JSON edit) - history is untouched, append-only, fully
      reversible. Board is down to 7 real active goals: 11, 12, 13, 28,
      30, 31, 34.

## Done, just noting for the record (this session, 2026-08-22)

- Clarifying-question flow for vague goals (generate_plan() can ask
  instead of invent), plan horizons widened 4 -> 7, resolve_duration()
  made properly public, "Generating plan..." loading state, Knowledge
  (RAG) room sketched in docs (not built) - see git log, commits
  76b5c49/face2fa/d387422 on multi-goal-ui-and-goal-id.
