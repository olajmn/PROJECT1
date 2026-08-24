# 06 — User Flows

> Phase 5 in [[00-project-brief]]. Builds on [[05-product]].

## Main flow (draft from the kickoff conversation)

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

## Refined as a closed loop (see [[04-hypothesis]] § Refined framing)

This isn't a one-time sequence — it's a loop that feeds back into memory
and starts again:

```
GOAL → PLAN → TODAY/RIGHT NOW → ACTION → USER FEEDBACK → REPLAN → ACTION → MEMORY ↺
```

"Prototype 0.1" (see [[09-mvp]]) is the smallest version of this that
actually closes the circle.

## Status in the code

- [x] "States a goal → agent creates a plan" — `backend/agent/specialized/plan.py`, see [[09-mvp]]
- [ ] Agent asks clarifying questions before planning
- [ ] Plan storage
- [ ] Today's action
- [ ] Feedback loop
- [ ] Replanning

## See also

- [[09-mvp]] — which part of the flow is actually built
- [[08-technical-architecture]]
