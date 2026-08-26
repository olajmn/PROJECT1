# Roadmap

Sequencing, so work doesn't start on everything at once. See
`DECISIONS.md` for the epistemic status of each underlying idea, and
`COMPONENT_MAP.md` for what each component actually is.

## Current

- This skeleton itself - agreed, being established now.
- The prototype's working loop (Vision → Goal → Plan → Action → Feedback,
  temporal understanding, persistence) - already real, keeps running
  unchanged in `backend/`/`devtools/` regardless of anything here.

## Next

1. **Component-by-component keep/move/rewrite/discard pass** over the
   prototype, using this skeleton as the map - the explicit next step this
   whole exercise was building toward (see the top-level `README.md`).
2. **Memory as a real capability** - not just unused raw JSON. Prerequisite
   for both Knowledge-style retrieval patterns and any future User
   Representation work, so it's worth doing before either.

## Later

- **Knowledge** - retrieval over user-supplied material.
- **Conversation as its own domain** - independent of a specific Goal's
  thread.
- **Decision's deterministic routing, made explicit** - it already exists
  in the prototype (inside `devtools/app.py`'s route logic); worth naming
  and separating out as its own thing before any intervention policy is
  considered.
- **Execution** - almost certainly by evaluating an existing external
  runtime to delegate to, rather than building tool-use/computer-use from
  scratch.

## Exploratory (not sequenced - revisit opportunistically, not on a schedule)

- User Representation / adaptive user model, and which mechanism (if any)
  it would start with.
- A proactive intervention policy on top of Decision.
- A minimal visual identity for the agent.
- The relational-continuity product hypothesis.

None of the exploratory items block anything in Next or Later - they're
independent bets, not prerequisites.
