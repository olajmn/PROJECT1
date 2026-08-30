# Session TODO

Working list of things noticed but not yet decided on/fixed, so
nothing gets lost while it's figured out what to tackle first. Not
part of the docs/ vault (that's permanent project documentation) -
this is scratch, meant to be cleared once everything on it is done or
has been moved into a proper dev log/decision entry (most recently
2026-08-24 - see [[06-development]] and [[05-decisions]] for what was
moved out before this cleared).

## Next session — pick ONE of these five, not more

Raised 2026-08-24, at the end of a long architecture-heavy session
(see [[06-development]] and [[03-architecture]] § Faculties)
- a ChatGPT reflection on that session's own summary put it well: the
  project now has "a conscious structure and a beginning architectural
  language... the next challenge is not to fall so in love with the
  architecture that building the agent itself stops." Explicit decision:
  next session picks ONE of these to actually build, not more naming/
  restructuring work.

**2026-08-25: Semantic understanding of time picked.** First piece
built - see [[06-development]] and [[03-architecture]] for what's
done vs. still open. The other four stay parked, unstarted:

- **Memory** - the agent starting to actively use its own history
  (`data_persistence.py` today is Infrastructure - pure persistence, understands
  nothing it stores; "Memory" as a real capability isn't built).
- **Better step hierarchy** - see the existing open item directly below;
  this is the same thing, just renamed by the same reflection.
- **Knowledge / RAG** - sketched in [[02-product]], not built.
- **Acting** - the agent actually doing things (making a file, calling
  an API), not just reasoning about what should happen - see
  [[06-development]]'s "agent actually doing things" entry.

## Open — noticed, not yet decided/fixed

- [ ] **Vertical/hierarchical step list, not one flat list per goal** -
      concrete trigger: "improve my diet" over 3 months produces
      steps like "Sep 06-Sep 22 Make a list of healthy grocery items" -
      a single step spanning 16 days, because today's step_count()/
      MIN_STEPS/MAX_STEPS (backend/foundation/time/) was tuned for
      single-session goals (a 20-minute goal breaking into ~15-minute
      steps), not multi-month ones, so a long goal's "steps" are really
      acting as coarse PHASES, not the granular actions they're meant
      to be. User's proposed shape: each step also carries its own
      smaller goal/horizon underneath it - closer to a real nested
      hierarchy (a `this_week` step has its own `today`-level sub-steps,
      etc) than today's one flat list stretched across the whole span.
      This is the SAME open question already sitting in
      docs/06-development.md under "Plan as an ordered step
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
      something that `parse_outcome()` reads as `goal_completed` (see
      frontend/app.py's /feedback) to actually mark it complete. This IS
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

