# 02 — Product

What the product is, concretely: job, primary surface, MVP shape, and
what is out of scope. Not how the system is built ([[03-architecture]])
or what the code looks like today ([[04-current-state]]). Product
direction settled in [[05-decisions]] #25; remaining wire rename is
[[goal-to-project-migration]] Phase B.

## Contents

- Product definition
- Primary surface and loop
- MVP
- Non-goals
- See also

## 1. Product definition

The product is a **Project** workspace. Its job is a **mental map** —
Start → waypoints → End — that the user co-builds with the agent.

- The **user steers** the line (chat, click, named beads via + / ×,
  Paste, Suggest).
- The agent **proposes** (one question or one concrete suggestion) and
  does not dump a syllabus or finish the middle for the user.
- **Time is optional** for co-building and for deepening the map — not
  the gate and not the spine.
- Persistence may still store records as goals (`goal_id`) until a later
  rename; the product language is Project.

The first user is the project owner, testing on themselves.

## 2. Primary surface and loop

**Home:** Projects (`/` → Projects page) — list | canvas (map) | chat
for the open project. Vision and Log (Completed / History / Sessions)
sit beside it. Free Conversation, Set Goal, and Steps are secondary
(“Other”).

### Co-build loop (current product)

```text
Name a Project (End clear enough to start)
↓
Optional horizons / nudge from the engine
↓
User builds or edits the map (+ / Paste / Suggest / focused chat)
↓
Chat under a selected waypoint (map focus)
↓
Feedback → agent proposes; user keeps steering the map
```

This replaces the earlier draft loop “goal → full plan → today’s
action → replan” as the **product** story. The engine may still fill
optional time horizons and a `now` nudge; those are not the map.

### What “done enough” means

A session succeeds when the user has a clearer map of *their* landmarks
than when they started — not when the agent has produced a complete
schedule or curriculum.

## 3. MVP

Smallest useful slice of the definition above:

- Create / open a Project on the Projects surface
- Coarse End clarity via Decide (ASK / SUGGEST / PLAN) without requiring
  a timeframe
- Empty or user-built WHAT map (`plan.progression`) — no agent dump of
  the middle on PLAN
- Chat with optional map focus; agent proposes, user edits
- Vision as optional broader direction; Log to look back

Accuracy of model wording is separate from “the loop works” — see
[[04-current-state]] and [[05-decisions]].

### Testing philosophy

> Can this help me orient a real project I would otherwise muddle through?

Not needed to test the core: mobile app, voice, cloud, multi-user,
advanced memory DB, or wiring every unused Module. Prefer real use over
more ideation.

## 4. Non-goals (for now)

- Agent that finishes the plan or teaches a full course in the middle
- Timeframe as a hard gate before any map
- Renaming `goal_id` / `/api/goals` before product feel is settled
  ([[goal-to-project-migration]] Phase B)
- Building every long-term capability menu item at once (old Planning /
  Memory / RAG sketches live in history docs; they are not this MVP)

## See also

- [[00-project-brief]]
- [[05-decisions]] #25
- [[goal-to-project-migration]]
- [[04-current-state]]
- [[03-architecture]]
