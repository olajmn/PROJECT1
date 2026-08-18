# 11 — Experiments

> Tests of [[04-hypothesis]] and product assumptions.

## Template

**Hypothesis tested:**
**Setup:** (who, how many, how)
**Result:**
**Learning:**
**Consequence:** (what do we change based on this?)

## Log

### 2026-08-18 — First live use: hallucinated detail

**Hypothesis tested:** Does `llama3.1:8b` (local Ollama) give reliable,
grounded replanning answers, not just structurally valid JSON?
**Setup:** Real usage by the project owner via `backend/devtools/app.py`.
Goal: "Read one book this month." After 2 feedback rounds (not done →
smaller step; done → next step), the agent's "right_now" action referred
to "chapter 11" of a specific book.
**Result:** Fabricated detail. The user never stated a book title, a
chapter, or any reading progress. The model invented a plausible-sounding
but ungrounded specific fact.
**Learning:** The mechanism (LLM call → save → display → replan) worked
perfectly — this is a **content reliability** failure, not an engineering
failure. Confirms the risk flagged when `llama3.1:8b` was chosen over
Claude (see [[12-decisions]]): smaller local models hallucinate more,
especially when asked to "sound concrete." An execution agent stating
false specifics with confidence could actively mislead the user, which
is worse than being vague.
**Consequence:** No fix applied yet — logged as a known limitation (see
[[09-mvp]] § Important distinction). Decided not to switch to Claude
right now to avoid cost during free/exploratory testing (see
[[../CONVENTIONS.md]] and the user's cost-sensitivity preference). Revisit
if hallucinations happen often enough to undermine trust in testing, or
before any real (non-owner) user tests the agent.

## See also

- [[04-hypothesis]]
- [[12-decisions]]
