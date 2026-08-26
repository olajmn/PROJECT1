# Component Map

Every component in this skeleton, its status, what it owns, and its
relationship to its neighbors. See `ARCHITECTURE.md` for the reasoning
behind the split, and `DECISIONS.md` for what's actually settled.

**Status key** - CURRENT (proven, working in the prototype), NEXT (a real,
identified gap, not hypothetical - just not built), FUTURE (a known,
named future need, not yet started), EXPLORATORY (a hypothesis; may or may
not end up built at all).

| Component | Status | Owns | Relationship |
|---|---|---|---|
| `vision/` | CURRENT | Optional, cross-Goal context - id+text | Sits above the operational loop; a Goal optionally references one |
| `goals/goal/` | CURRENT | Goal identity/lifecycle | Root of the operational loop; owns one Plan at a time |
| `goals/plan/` | CURRENT | Strategy for one Goal across time horizons | Belongs to one Goal; its narrowest horizon is Action |
| `goals/action/` | CURRENT | The user's immediate next step | Part of Plan's shape, modeled as its own responsibility - see `ARCHITECTURE.md` |
| `goals/feedback/` | CURRENT | Parsing what happened into a structured signal | Closes the loop back into Plan (replanning) |
| `conversation/` | NEXT | Raw message exchange, independent of what it resolves into | Upstream of Interpretation/Parsing; feeds Goals, Knowledge, or neither |
| `memory/` | NEXT | The agent's own raw operational history | Source of truth for User Representation; read by Reasoning |
| `knowledge/` | FUTURE | User-supplied external material | Separate corpus from Memory; read by Reasoning |
| `user_model/` | EXPLORATORY | Derived, adaptive representation of this user's patterns | Reads Memory only; informs Reasoning and Decision |
| `decision/` | CURRENT (routing) / EXPLORATORY (intervention) | What happens next, given parsed input + state | Sits between Reasoning and Action/Execution |
| `execution/` | FUTURE | The agent performing something in the real world | Distinct from Action - see `ARCHITECTURE.md` |
| `reasoning/` | NEXT | The one boundary every LLM call passes through | Called by Planning today; potentially Decision/Knowledge later |
| `world/` | FUTURE | Live external information (weather, calendar, etc.) | Deliberate empty placeholder, unchanged from the prototype |
| `foundation/` | CURRENT | The Domain/Faculty/Infrastructure/Pipeline lens itself, and proven Faculties | Cross-cutting - not part of the operational loop |
| `infrastructure/` | CURRENT | Persistence and other shared technical machinery | Used by every component that stores or moves data |
| `interface/` | CURRENT | The presentation layer a person actually interacts with | Swappable client; not part of the agent's own cognition |
| `interface/visual_identity/` | EXPLORATORY | A minimal, stable visual identity for the agent | One possible expression of `interface/`, not a separate component |

## Explicitly not components

Rejected as their own top-level components during this pass, and why:

| Considered | Resolution |
|---|---|
| Expectation / Discrepancy | Folded into `user_model/` - it's the *function* User Representation performs (predict → observe → compare → update), not a separate responsibility |
| Neural Network | A possible future mechanism inside `user_model/`, never a component |
| RAG | A possible future mechanism inside `memory/` and/or `knowledge/`, never a component |
| Embeddings | Same as RAG - a mechanism, not a component |
| Vector database | An implementation technology a retrieval mechanism might use, two levels more concrete than architecture |

## Where mechanisms plug in

Kept out of the folder structure entirely - listed here so the question
"where would X eventually go" has one answer instead of drifting per
conversation.

| Mechanism | Where it would plug in | Component README with the fuller reasoning |
|---|---|---|
| Exponential moving average / Bayesian updating | Inside `user_model/`, as the first, simplest way to turn Memory observations into an expectation | `user_model/README.md` |
| Small neural network | A *later* possible upgrade inside `user_model/`, only once simpler statistics prove insufficient | `user_model/README.md` |
| Deterministic filtering (keyword, date, goal) | Inside `memory/`, as the first retrieval mechanism | `memory/README.md` |
| Embeddings / vector search | A later upgrade inside `memory/` (if filtering proves insufficient) and/or `knowledge/` (likely needed sooner, given more heterogeneous material) | `memory/README.md`, `knowledge/README.md` |
| LLM calls (any provider) | Exclusively through `reasoning/` - no other component calls a model directly | `reasoning/README.md` |
