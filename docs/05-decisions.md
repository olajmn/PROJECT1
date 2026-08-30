# 05 — Decisions

> Decision log — why we chose what we chose, so we don't re-litigate it in three months. Renamed 2026-08-25 from the original `12-decisions.md` (content unchanged; only cross-references to other renamed docs updated — dated entries otherwise describe the project as it was on that date, including old code paths, same convention this log already followed for itself).

## Template

**Decision:**
**Date:**
**Alternatives considered:**
**Why this choice:**
**Reversible?**

## 1. 2026-08-20 — Replace the Yes/Still working on it/No/Goal complete buttons with a classified free-text note

**Alternatives considered:** keep the four buttons as the only signal (note stays a footnote); let the LLM classify the free-text note into an outcome; a deterministic phrase-matcher, same approach as `backend/timeperiod.py`'s `resolve_duration()` (at the time this was written, that logic still lived in `goal_to_plan.py` as `_resolve_duration()` — both since renamed/moved).
**Why this choice:** the goal was to stop requiring what actually happened to be mapped onto one of four fixed boxes before writing anything, while explicitly keeping that decision away from an LLM — classifying true/false from ambiguous text is the same kind of guess that produced this project's hallucination findings, just one step earlier in the pipeline. `backend/outcome_classifier.py` recognizes a growing list of known phrases per outcome (no model call) and returns `None` for anything it doesn't recognize; app.py's `/feedback` route treats `None` the same as an explicit "still working on it" — a safe check-in, never a guess toward the two outcomes that change state (done -> replan, goal_done -> permanent). Built as its own module specifically so the phrase lists can grow from real usage without touching app.py or goal_to_plan.py.
**Trade-off:** phrasing the classifier doesn't recognize (e.g. "I sent 2 of 4 applications") gets treated as a no-op check-in even when it actually contains real signal — safe, but the note itself is currently the only place that nuance is preserved (it's not lost, just not acted on automatically).
**Reversible?** Yes — `classify_outcome()` is a single pure function; reverting to explicit buttons or swapping in an LLM-based classifier both are localized changes, not a redesign.

## 2. 2026-08-18 — LLM backend: Ollama (local) instead of Anthropic Claude

**Alternatives considered:** Anthropic Claude API (`claude-opus-5`), a
local model via Ollama.
**Why:** The Anthropic key that was set was invalid, and a completely free/keyless option was worth exploring while learning. Ollama runs locally, no key or internet required.
**Trade-off:** `llama3.1:8b` is weaker at reasoning/planning than Claude Opus 5. Both SDKs (`ollama`, `anthropic`) are kept installed in `requirements.txt`, so switching to Claude later is a small code change, see [[03-architecture]].
**Reversible?** Yes, trivially.

## 3. 2026-08-18 — Project language: English (code and docs)

**Why:** Standard practice, makes the whole project (code + documentation) easier to share/open up later. See `../CONVENTIONS.md`.
**Reversible?** Yes, but costly to change once the project grows.

## 4. 2026-08-18 — Isolated Python virtual environment (`.venv/`)

**Why:** The machine has two competing Python 3.14 installations that caused confusion about where packages get installed. A project-local venv solves this permanently and is standard practice anyway.
**Reversible?** Yes.

## 5. 2026-08-18 — Storage: local plaintext JSON, history not overwrite

**Alternatives considered:** overwrite a single "current plan" file, keep full history, use a real database.
**Why:** "Memory" is a named differentiator in [[01-research]] — an agent that forgets the previous plan the moment a new goal is set isn't better than a todo app. A real database is overkill before the hypothesis is validated, so we start with an append-only JSON history file.
**Privacy trade-off (explicit, revisit later):** the file is unencrypted on disk. Acceptable for a single-user local MVP on a personal machine. Two mitigations applied now: `data/` is git-ignored (goals/plans must never end up in a public repo even after the code itself is), and this decision is logged so it isn't forgotten once the project has multiple users or lives in the cloud — at that point this needs encryption at rest, proper auth, and a real privacy policy.
**Reversible?** Yes — swapping JSON for a database later doesn't change the rest of the architecture (see [[03-architecture]]).

## 6. 2026-08-18 — Reframe: the agent is the product, not a planner app

**Why:** Planning is one capability the agent uses, not the product itself. Reframes the hypothesis as testing a continuous loop (goal → plan → action → feedback → replan → memory), not a one-time plan generator. Arrived at independently in a parallel ChatGPT discussion — treated as a useful consistency check. See [[06-development]] § Hypothesis, Refined framing.
**Reversible?** Yes — doesn't change any code, only framing/priorities.

## 7. 2026-08-18 — Testing takes priority over further ideation

**Why:** A lot of time went into exploring what the project *could* become (memory architecture, cloud, web UI, aggregation, multi-device). None of that is needed to test the core hypothesis. Decision: finish Prototype 0.1 (the feedback/replan loop) and test on the project owner first, before any further scope expansion. See [[02-product]] § Testing philosophy.
**Reversible?** Yes, but the point is specifically to resist reversing it prematurely.

## 8. 2026-08-18 — Static HTML view (`backend/view.py`) for personal use only

**Why:** the user thinks visually, not abstractly — raw JSON/terminal text makes it hard to follow what the agent is actually doing. This is explicitly a personal debugging/orientation tool, not the product's frontend — no server, no JS, regenerated on demand from `data/plans.json`. Does not contradict "testing over further ideation" (see above) because it isn't a feature, it's a way to see existing data.
**Reversible?** Yes, trivially — delete the file, nothing else depends on it.

## 9. 2026-08-18 — Cleanup pass: fixed correctness/reuse issues, skipped premature efficiency optimization

**Ran `/code-review` + `/simplify` (4 parallel angles) on `backend/`.** Fixed: `today.py` crash on legacy string-format plans (now normalized once in `storage.py`, not special-cased per caller), unvalidated LLM JSON output (schema now checked in `goal_to_plan.py` against a single `PLAN_KEYS` definition), `data/plans.json` corruption risk on a crashed write (now an atomic temp-file+rename), missing-field crashes in the Flask routes, unescaped HTML in the hand-built history page (replaced with a Jinja template — autoescaped, same as the rest of the app), duplicated CSS/HTML-building logic between `view.py` and `app.py`.

**Skipped:** the efficiency agent's finding that every save/read does a full read-and-rewrite of `plans.json` (O(n) per operation). Fixing this properly means changing the storage format (e.g. append-only JSONL) — real behavior change for real cost, at a scale (single user, ~10 records, human click speed) where the cost is negligible. Matches the already-documented "JSON is sufficient for MVP, don't over-engineer" stance in [[03-architecture]] § Architectural principles. Revisit only if history size or request volume actually becomes a problem.
**Reversible?** Yes.

## 10. 2026-08-20 — Built an auto-generated architecture diagram anyway, kept outside `backend/`

**Alternatives considered:** keep the architecture diagram fully hand-maintained (matches "don't build it before it's needed" — this log's own recurring principle); build a code-to-diagram generator now.
**Why this choice:** built specifically in response to the overengineering concern above, with a specific future intent — lift it out of this repo later as an external tool/capability the agent itself could call on (see [[06-development]] § Parking Lot, "Tools / APIs the agent can use"). Built as `tools/architecture_mapper/` (see its own README.md), not inside `backend/`: it only uses Python's `ast` module on the target source, imports nothing from `backend`, and knows nothing project-specific — a deliberate boundary so it stays extractable intact.
**Trade-off:** it's a second thing to maintain, and it only ever describes the NOW section (functions/imports it can see in code) — it has no way to represent `docs/03-architecture.md`'s VISION section, so `docs/03-architecture.drawio` stays hand-maintained as the full source of truth; the generator's output (`tools/architecture_mapper/output/`, git-ignored) is a cross-check, not a replacement.
**Reversible?** Yes — it's fully self-contained in one folder with no inbound or outbound imports to the rest of the project, by design.

## 11. 2026-08-19 — Write goals in English, don't switch LLM backend yet

**Alternatives considered:** keep writing goals in Norwegian and accept the failures, switch to Claude API now, write goals in English.
**Why:** Norwegian goal text causes severe, reproducible hallucination in `llama3.1:8b` (entire responses disconnected from the actual goal — see [[06-development]] § Experiments, 2026-08-19). English phrasing of the identical goal produced grounded, sensible answers. Writing goals in English sidesteps the failure immediately, at zero cost, and doesn't block starting the real usage test that's been the priority all evening.
**Trade-off:** the user thinks/writes naturally in Norwegian; this is a real, felt friction, not a free workaround.
**Reversible?** Yes, trivially — revisit switching to Claude (better multilingual handling) if English-only friction becomes a real problem, per the already-logged Ollama-vs-Claude decision above.

## 12. 2026-08-21 — Don't recognize bare 4-digit clock times ("1400")

**Alternatives considered:** recognize a bare 4-digit number as a 24-hour clock time whenever it's a plausible time (0000-2359); require a signal word first ("kl 1400"/"at 1400"); don't recognize it at all, only colon-separated ("14:00") and 12-hour ("2pm"/"1 o'clock") forms.
**Why this choice:** a bare number carries no signal of its own — the user's own example, "1500kr" (a price), is indistinguishable from "1500" the clock time without reading the surrounding text, and the same ambiguity applies to quantities ("1400 meter", "1400 kalorier") and years. This is the same shape of risk `_matched_month_name()` already found and fixed ("I may go" silently resolving to next May) — a bare match doesn't fail honestly here, it confidently states a wrong answer, which is worse than not recognizing it at all. `"14:00"` (colon) and `"2pm"`/`"1 o'clock"` (explicit suffix) stay recognized because both carry their own unambiguous signal; nothing else does.
**Trade-off:** "kl 1400" (a real, common way to write a time, especially in Norwegian/military notation) stays unrecognized — "given, not parsed/verified by code" — rather than risk a wrong answer dressed up as a right one.
**Reversible?** Yes — if this turns out to matter enough in real use, the signal-word option ("kl"/"at" + 4 digits) is the safer middle ground to revisit, not the bare-number option.

## 13. 2026-08-21 — Remove YEAR_FRACTIONS ("half a year"/"quarter of a year")

**Alternatives considered:** keep `YEAR_FRACTIONS` as-is (4th entry in `_FRACTION_TABLES` alongside hour/minute/day); keep the table but drop it from recognition; remove it entirely.
**Why this choice:** questioned whether the whole named-fraction mechanism ("half an hour" etc., alongside the already-working numeric `DURATION_LENGTH_RE`) was worth its cost at all — concluded it earns its place for hour/minute/day because that's genuinely how people phrase those durations in speech ("half an hour" more than "30 minutes"), but year didn't clear the same bar: `MONTH_NAMES` (section 2) already names a year's parts, and a *span* like "half a year" resolving to "6 months from now" wasn't judged to add real value over just writing "6 months" (already handled by `DURATION_LENGTH_RE`).
**Trade-off:** "half a year"/"quarter of a year" now fall through to "given, not parsed/verified by code" instead of resolving — an honest answer, not a wrong one, just a narrower one than before.
**Reversible?** Yes, trivially — re-add `YEAR_FRACTIONS` to `time_segments.py`, put "year" back in `NAMED_FRACTION_RE`'s alternation and `_FRACTION_TABLES`, and re-add the `_add_months()` branch `_named_fraction_end()` used to have for it.

## 14. 2026-08-22 — Not moving to SQL; future personal knowledge base gets RAG, not a database

**Alternatives considered:** migrate `data/plans.json` to SQL now; migrate to SQL once the project grows into a multi-domain/"advanced" agent; use SQL as the retrieval mechanism for a future personal knowledge base (user-supplied documents the agent can draw on).
**Why this choice:** SQL earns its cost (schema, migrations, an opaque binary file instead of a readable one) when data is large AND the access pattern needs real relational queries (joins, multi-criteria filtering) or concurrent writers — none of which this project has: one user, one machine, ~100 records, and every actual lookup so far ("latest record for this goal_id", "group by active/completed") is already a plain, fast Python scan. This also runs directly against the project's own Data Ownership principle ([[03-architecture]] § Architectural principles) — a human-readable file the user can open and inspect without the app — which a SQL file doesn't give up easily. Separately, discussed extending the agent to multiple life-domains (health/work/finance) reasoning about each other — concluded that's a context-passed-to-the-prompt problem (a `domain` field + a short cross-domain summary handed to the model), not a JOIN, so it doesn't move the SQL calculus either. Separately again, discussed a future personal knowledge base (user-supplied documents, e.g. "text files with documented science") — concluded that's a RAG (Retrieval-Augmented Generation) problem, retrieved by embedding similarity, not exact-match SQL querying — see [[03-architecture]] § Knowledge for the sketched design (flat file of chunk+vector pairs, Ollama embeddings, brute-force similarity search — no vector database either, for the same "simplest thing that works at this scale" reasoning).
**Trade-off:** none of this is free forever — the doc above names the concrete trigger for each piece (felt query complexity for goals/plans, felt brute-force search slowness for the knowledge base) rather than a timeline, on purpose: revisit when the trigger is real, not on a schedule.
**Reversible?** Yes — nothing built tonight commits to a storage format that would need un-migrating; this is a decision about what to build next, not a lock-in.

## 15. 2026-08-18 — Local-first architecture for multi-device sync, not blockchain

**Alternatives considered:** blockchain-based consensus for multi-device sync; a conventional server-owns-the-data model; local-first architecture with end-to-end encryption.
**Why this choice:** the actual problem is two-fold — (1) a new device should be able to get the full agent back (history, context) via just a password/key, without the server operator being able to read the data, and (2) no single company should be able to lock the user out of or control access to their own data. Blockchain solves consensus among mutually-distrusting *strangers* via a public ledger — the wrong tool here both because "public" is the opposite of private, and because the actual problem is ownership/lock-out, not consensus. End-to-end encryption (the Bitwarden/1Password/Signal pattern — key derived locally from password, only the encrypted blob ever uploaded, server never sees plaintext) solves (1). Local-first (the user's own device always holds a complete copy, data stays in an open format, any sync server is a replaceable relay never the owner of the truth) solves (2).
**Trade-off:** requires a real backend + account system to build at all — not an MVP concern, tracked in [[06-development]] § Parking Lot.
**Reversible?** Yes — the project is already 100% local-first today by construction (no server exists yet); this is a design goal to preserve when sync is eventually added, not a commitment already built.

## 16. 2026-08-24 — Faculty categorization: reuse, understanding, and Infrastructure as a separate category

**Alternatives considered:** treat any broadly reused code as a Faculty; treat any code with a plausible conceptual name as a Faculty; or require a module to be both genuinely reusable and represent a capability through which the agent understands or interprets something.
**Why this choice:** a Faculty is not simply a reusable module, nor is it a conceptual label for a topic. It is a reusable capability through which the agent can understand or interpret something.

This creates a distinction between Domains and Faculties:

- A **Domain** is an area of responsibility or subject matter the system operates on.
- A **Faculty** is a reusable capability for understanding or interpreting something within or across those areas.
- A Faculty does not need to exist for every Domain. It should emerge when a capability proves genuinely reusable, rather than being predetermined as part of the architecture.
- **Infrastructure** is shared technical machinery that may be widely reused but does not itself represent something the agent understands.

Time provides the first concrete example. Time is a Domain because the system operates on durations, timeframes, dates and deadlines. Temporal understanding is a Faculty because it provides the reusable capability to interpret temporal expressions and durations. The two are related, but they are not the same thing.

The same principle explains why `infrastructure/data_persistence.py` is Infrastructure rather than a Faculty. It is reused broadly by every Domain and by `devtools/app.py` directly, but it does not understand what the data represents — it only stores and retrieves it.

Similarly, `outcome_classifier.py` is not currently a Faculty merely because it shares a deterministic phrase-matching *pattern* with `foundation/time/time_logic/phrase_matching.py`. It is currently specific to Goal's feedback flow and has not demonstrated reuse as a general agent capability.

The rule is therefore not "reused code = Faculty." The question is: does this represent a genuinely reusable capability through which the agent understands or interprets something? If not, it should not be elevated to Faculty status merely because it has a good name or is technically reusable.

Also decided the same day: `world/` remains separate from `foundation/`. World represents live external information and services; foundation represents the agent's own reusable understanding and capabilities. They may both sit outside immediate reasoning, but they serve fundamentally different purposes.
**Reversible?** Yes — these are architectural categorization principles rather than load-bearing implementation decisions. A module can be reclassified or moved later without requiring a redesign.

## 17. 2026-08-26 — Represent Vision as a separate, lightweight id+text store, not a hierarchy

**Alternatives considered:** duplicate the Vision's text directly onto every Goal record that shares it (no separate store, no id); a fully relational structure (a Vision "owns" its Goals, cascading updates/deletes, parent-child constraints); a separate, lightweight store (`data/visions.json`, `{id, text}`) with Goal records carrying an optional `vision_id` reference.
**Why this choice:** duplicating text was rejected for the same reason Goal identity itself moved off free-text matching years ago in this project's own history (see the 2026-08-20 decision on `goal_id`) — two goals with independently-typed, slightly different vision wording would silently fork into two visions instead of sharing one, the exact bug that decision already fixed once. A full relational structure was rejected as solving a problem that doesn't exist yet: [[03-architecture]] already discussed extending the agent to "multiple life-domains reasoning about each other" (decision #14 above) and concluded that should be a context-passed-to-the-prompt problem, not a JOIN — a Vision doesn't need to cascade anything, own anything, or enforce referential integrity beyond "does this id exist." The chosen shape — a small separate store plus an optional foreign-key-style id — is exactly the pattern `goal_id` itself already uses, applied to a second, much smaller identity.
**Trade-off:** no editing or deleting an existing Vision yet (create-only) — a typo in a Vision's text has to be lived with or a new one created, until real usage shows whether that's worth building. No Vision text is supplied to the LLM yet either — `generate_plan()`/`replan()` both ignore `vision_id` completely; the relationship, if ever built, is meant to stay "Vision contextualizes Goals," never "Vision generates Goals" (see [[03-architecture]] § Vision).
**Reversible?** Yes — `save_vision()`/`load_visions()`/`get_vision()` are three small, pure functions in `data_persistence.py`; moving to a richer structure later (or dropping Vision entirely) touches an optional field and a handful of call sites, not a schema migration.

## 18. 2026-08-30 — Remove `docs/03-architecture.drawio`; supersede decision #10's "full source of truth" framing

**Alternatives considered:** keep `03-architecture.drawio` hand-maintained alongside the new `04-current-state.md` diagram (two visual artifacts describing overlapping ground); keep it only for the VISION material NOW can't show; remove it and rely on `04-current-state.md` § Visual Overview for current structure, with `03-architecture.md` § 6 (Long-Term Architecture) covering VISION in prose/ASCII form instead.
**Why this choice:** `tools/architecture_mapper/` (the auto-generated cross-check decision #10 describes) was already removed as an unneeded experiment. With it gone, `03-architecture.drawio` had no cross-check and had drifted into the same problem `04-current-state.md`'s intro already warns about for prose — a second, separately-maintained description of the system that goes stale unless actively kept in sync. `04-current-state.md` is now a single combined document (Mermaid diagram + written structure), built and verified against the actual code rather than hand-drawn, and is the file every other doc already points to for "what's true right now."
**Why decision #10 no longer applies:** decision #10 said `03-architecture.drawio` "stays hand-maintained as the full source of truth" for both VISION and NOW, precisely because the auto-generated cross-check "only ever describes the NOW section." That reasoning depended on the auto-generated cross-check existing. It doesn't anymore, and NOW now has its own maintained diagram in `04-current-state.md` instead. Decision #10's own text is left unchanged, as history — this entry supersedes its conclusion, not its record of what was true on 2026-08-20.
**Trade-off:** VISION (§ 6 of `03-architecture.md`, the not-yet-built long-term system) has no diagram of its own anymore, only the existing ASCII sketch. Acceptable — nothing there is built yet, so there is no current structure to keep a second diagram in sync with.
**Reversible?** Yes — nothing about `04-current-state.md`'s diagram depends on `03-architecture.drawio` not existing; a VISION-specific diagram could be added back later if § 6 ever gets built out enough to need one.

## See also

- [[03-architecture]]
- [[06-development]]
