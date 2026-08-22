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

## 2026-08-20 — Replace the Yes/Still working on it/No/Goal complete buttons with a classified free-text note

**Alternatives considered:** keep the four buttons as the only signal
(note stays a footnote); let the LLM classify the free-text note into
an outcome; a deterministic phrase-matcher, same approach as
goal_to_plan.py's `_resolve_duration()`.
**Why this choice:** the user wanted to stop having to map what
actually happened onto one of four fixed boxes before writing
anything, but explicitly did not want that decision handed to an LLM -
classifying true/false from ambiguous text is the same kind of guess
that produced this project's hallucination findings, just one step
earlier in the pipeline. `backend/outcome_classifier.py` recognizes a
growing list of known phrases per outcome (no model call) and returns
`None` for anything it doesn't recognize; app.py's `/feedback` route
treats `None` the same as an explicit "still working on it" - a safe
check-in, never a guess toward the two outcomes that change state
(done -> replan, goal_done -> permanent). Built as its own module
specifically so the phrase lists can grow from real usage without
touching app.py or goal_to_plan.py.
**Trade-off:** phrasing the classifier doesn't recognize (e.g. "I sent
2 of 4 applications") gets treated as a no-op check-in even when it
actually contains real signal - safe, but the note itself is currently
the only place that nuance is preserved (it's not lost, just not acted
on automatically).
**Reversible?** Yes - `classify_outcome()` is a single pure function;
reverting to explicit buttons or swapping in an LLM-based classifier
both are localized changes, not a redesign.

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

## 2026-08-20 — Built an auto-generated architecture diagram anyway, kept outside `backend/`

**Alternatives considered:** keep the architecture diagram fully
hand-maintained (matches "don't build it before it's needed" -
`docs/12-decisions.md`'s own recurring principle); build a code-to-diagram
generator now.
**Why this choice:** the user explicitly asked for it after hearing the
overengineering concern, with a specific future intent - lift it out of
this repo later as an external tool/capability the agent itself could
call on (see [[13-ideas-parking-lot]] "Tools / APIs the agent can use").
Built as `tools/architecture_mapper/` (see its own README.md), not
inside `backend/`: it only uses Python's `ast` module on the target
source, imports nothing from `backend`, and knows nothing project-
specific - a deliberate boundary so it stays extractable intact.
**Trade-off:** it's a second thing to maintain, and it only ever
describes the NOW section (functions/imports it can see in code) - it
has no way to represent `docs/08-technical-architecture.md`'s VISION
section, so `docs/08-architecture.drawio` stays hand-maintained as the
full source of truth; the generator's output
(`tools/architecture_mapper/output/`, git-ignored) is a cross-check, not
a replacement.
**Reversible?** Yes - it's fully self-contained in one folder with no
inbound or outbound imports to the rest of the project, by design.

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

## 2026-08-21 — Don't recognize bare 4-digit clock times ("1400")

**Alternatives considered:** recognize a bare 4-digit number as a
24-hour clock time whenever it's a plausible time (0000-2359); require
a signal word first ("kl 1400"/"at 1400"); don't recognize it at all,
only colon-separated ("14:00") and 12-hour ("2pm"/"1 o'clock") forms.
**Why this choice:** a bare number carries no signal of its own - the
user's own example, "1500kr" (a price), is indistinguishable from
"1500" the clock time without reading the surrounding text, and the
same ambiguity applies to quantities ("1400 meter", "1400 kalorier")
and years. This is the same shape of risk `_matched_month_name()`
already found and fixed ("I may go" silently resolving to next May) -
a bare match doesn't fail honestly here, it confidently states a wrong
answer, which is worse than not recognizing it at all. `"14:00"`
(colon) and `"2pm"`/`"1 o'clock"` (explicit suffix) stay recognized
because both carry their own unambiguous signal; nothing else does.
**Trade-off:** "kl 1400" (a real, common way to write a time,
especially in Norwegian/military notation) stays unrecognized -
"given, not parsed/verified by code" - rather than risk a wrong answer
dressed up as a right one.
**Reversible?** Yes - if this turns out to matter enough in real use,
the signal-word option ("kl"/"at" + 4 digits) is the safer middle
ground to revisit, not the bare-number option.

## 2026-08-21 — Remove YEAR_FRACTIONS ("half a year"/"quarter of a year")

**Alternatives considered:** keep `YEAR_FRACTIONS` as-is (4th entry in
`_FRACTION_TABLES` alongside hour/minute/day); keep the table but drop
it from recognition; remove it entirely.
**Why this choice:** questioned whether the whole named-fraction
mechanism ("half an hour" etc., alongside the already-working numeric
`DURATION_LENGTH_RE`) was worth its cost at all - concluded it earns
its place for hour/minute/day because that's genuinely how people
phrase those durations in speech ("half an hour" more than "30
minutes"), but year didn't clear the same bar: `MONTH_NAMES` (section
2) already names a year's parts, and a *span* like "half a year"
resolving to "6 months from now" wasn't judged to add real value over
just writing "6 months" (already handled by `DURATION_LENGTH_RE`).
**Trade-off:** "half a year"/"quarter of a year" now fall through to
"given, not parsed/verified by code" instead of resolving - an honest
answer, not a wrong one, just a narrower one than before.
**Reversible?** Yes, trivially - re-add `YEAR_FRACTIONS` to
`timesegments.py`, put "year" back in `NAMED_FRACTION_RE`'s
alternation and `_FRACTION_TABLES`, and re-add the `_add_months()`
branch `_named_fraction_end()` used to have for it.

## 2026-08-22 — Not moving to SQL; future personal knowledge base gets RAG, not a database

**Alternatives considered:** migrate `data/plans.json` to SQL now;
migrate to SQL once the project grows into a multi-domain/"advanced"
agent; use SQL as the retrieval mechanism for a future personal
knowledge base (user-supplied documents the agent can draw on).
**Why this choice:** SQL earns its cost (schema, migrations, an opaque
binary file instead of a readable one) when data is large AND the
access pattern needs real relational queries (joins, multi-criteria
filtering) or concurrent writers - none of which this project has: one
user, one machine, ~100 records, and every actual lookup so far ("latest
record for this goal_id", "group by active/completed") is already a
plain, fast Python scan. This also runs directly against the project's
own Data Ownership principle
([[08-technical-architecture]] § Data Ownership) - a human-readable
file the user can open and inspect without the app - which a SQL file
doesn't give up easily. Separately, discussed extending the agent to
multiple life-domains (health/work/finance) reasoning about each other
- concluded that's a context-passed-to-the-prompt problem (a `domain`
field + a short cross-domain summary handed to the model), not a JOIN,
so it doesn't move the SQL calculus either. Separately again, discussed
a future personal knowledge base (user-supplied documents, e.g. "text
files with documented science") - concluded that's a RAG (Retrieval-
Augmented Generation) problem, retrieved by embedding similarity, not
exact-match SQL querying - see [[07-features]] § Knowledge (RAG over
user documents) for the sketched design (flat file of chunk+vector
pairs, Ollama embeddings, brute-force similarity search - no vector
database either, for the same "simplest thing that works at this
scale" reasoning).
**Trade-off:** none of this is free forever - the doc above names the
concrete trigger for each piece (felt query complexity for goals/plans,
felt brute-force search slowness for the knowledge base) rather than a
timeline, on purpose: revisit when the trigger is real, not on a
schedule.
**Reversible?** Yes - nothing built tonight commits to a storage format
that would need un-migrating; this is a decision about what to build
next, not a lock-in.

## See also

- [[08-technical-architecture]]
- [[10-development]]
