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
- *(add more ideas here as they come up — don't build them yet)*
