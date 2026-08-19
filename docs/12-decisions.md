# 12 — Decisions

> Decision log — why we chose what we chose, so we don't re-litigate it
> in three months.

## Template

**Decision:**
**Date:**
**Alternatives considered:**
**Why this choice:**
**Reversible?**

---

## 2026-08-18 — LLM backend: Ollama (local) instead of Anthropic Claude

**Alternatives considered:** Anthropic Claude API (`claude-opus-5`), a
local model via Ollama.
**Why:** The Anthropic key that was set was invalid, and the user wanted
to explore a completely free/keyless option while learning. Ollama runs
locally, no key or internet required.
**Trade-off:** `llama3.1:8b` is weaker at reasoning/planning than Claude
Opus 5. Both SDKs (`ollama`, `anthropic`) are kept installed in
`requirements.txt`, so switching to Claude later is a small code change,
see [[08-technical-architecture]].
**Reversible?** Yes, trivially.

## 2026-08-18 — Project language: English (code and docs)

**Why:** Standard practice, makes the whole project (code + documentation)
easier to share/open up later. See `../CONVENTIONS.md`.
**Reversible?** Yes, but costly to change once the project grows.

## 2026-08-18 — Isolated Python virtual environment (`.venv/`)

**Why:** The machine has two competing Python 3.14 installations that
caused confusion about where packages get installed. A project-local
venv solves this permanently and is standard practice anyway.
**Reversible?** Yes.

## 2026-08-18 — Storage: local plaintext JSON, history not overwrite

**Alternatives considered:** overwrite a single "current plan" file, keep
full history, use a real database.
**Why:** "Memory" is a named differentiator in [[03-competitors]] — an
agent that forgets the previous plan the moment a new goal is set isn't
better than a todo app. A real database is overkill before the hypothesis
is validated, so we start with an append-only JSON history file.
**Privacy trade-off (explicit, revisit later):** the file is unencrypted
on disk. Acceptable for a single-user local MVP on a personal machine.
Two mitigations applied now: `data/` is git-ignored (goals/plans must
never end up in a public repo even after the code itself is), and this
decision is logged so it isn't forgotten once the project has multiple
users or lives in the cloud — at that point this needs encryption at
rest, proper auth, and a real privacy policy.
**Reversible?** Yes — swapping JSON for a database later doesn't change
the rest of the architecture (see [[08-technical-architecture]]).

## 2026-08-18 — Reframe: the agent is the product, not a planner app

**Why:** Planning is one capability the agent uses, not the product
itself. Reframes the hypothesis as testing a continuous loop (goal →
plan → action → feedback → replan → memory), not a one-time plan
generator. Arrived at independently in a parallel ChatGPT discussion —
treated as a useful consistency check. See [[04-hypothesis]] § Refined framing.
**Reversible?** Yes — doesn't change any code, only framing/priorities.

## 2026-08-18 — Testing takes priority over further ideation

**Why:** A lot of time went into exploring what the project *could*
become (memory architecture, cloud, web UI, aggregation, multi-device).
None of that is needed to test the core hypothesis. Decision: finish
Prototype 0.1 (the feedback/replan loop) and test on the project owner
first, before any further scope expansion. See [[09-mvp]] § Testing philosophy.
**Reversible?** Yes, but the point is specifically to resist reversing it
prematurely.

## 2026-08-18 — Static HTML view (`backend/view.py`) for personal use only

**Why:** the user thinks visually, not abstractly — raw JSON/terminal
text makes it hard to follow what the agent is actually doing. This is
explicitly a personal debugging/orientation tool, not the product's
frontend — no server, no JS, regenerated on demand from
`data/plans.json`. Does not contradict "testing over further ideation"
(see above) because it isn't a feature, it's a way to see existing data.
**Reversible?** Yes, trivially — delete the file, nothing else depends on it.

## 2026-08-18 — Cleanup pass: fixed correctness/reuse issues, skipped premature efficiency optimization

**Ran `/code-review` + `/simplify` (4 parallel angles) on `backend/`.**
Fixed: `today.py` crash on legacy string-format plans (now normalized
once in `storage.py`, not special-cased per caller), unvalidated LLM
JSON output (schema now checked in `goal_to_plan.py` against a single
`PLAN_KEYS` definition), `data/plans.json` corruption risk on a crashed
write (now an atomic temp-file+rename), missing-field crashes in the
Flask routes, unescaped HTML in the hand-built history page (replaced
with a Jinja template — autoescaped, same as the rest of the app),
duplicated CSS/HTML-building logic between `view.py` and `app.py`.

**Skipped:** the efficiency agent's finding that every save/read does a
full read-and-rewrite of `plans.json` (O(n) per operation). Fixing this
properly means changing the storage format (e.g. append-only JSONL) —
real behavior change for real cost, at a scale (single user, ~10 records,
human click speed) where the cost is negligible. Matches the
already-documented "JSON is sufficient for MVP, don't over-engineer"
stance in [[08-technical-architecture]] § Memory & Data Architecture.
Revisit only if history size or request volume actually becomes a
problem.
**Reversible?** Yes.

## 2026-08-19 — Write goals in English, don't switch LLM backend yet

**Alternatives considered:** keep writing goals in Norwegian and accept
the failures, switch to Claude API now, write goals in English.
**Why:** Norwegian goal text causes severe, reproducible hallucination
in `llama3.1:8b` (entire responses disconnected from the actual goal -
see [[11-experiments]], 2026-08-19). English phrasing of the identical
goal produced grounded, sensible answers. Writing goals in English
sidesteps the failure immediately, at zero cost, and doesn't block
starting the real usage test that's been the priority all evening.
**Trade-off:** the user thinks/writes naturally in Norwegian; this is a
real, felt friction, not a free workaround.
**Reversible?** Yes, trivially - revisit switching to Claude (better
multilingual handling) if English-only friction becomes a real problem,
per the already-logged Ollama-vs-Claude decision above.

## See also

- [[08-technical-architecture]]
- [[10-development]]
