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

The same principle explains why `store/data_persistence.py` (was `infrastructure/…`) is Infrastructure-category rather than a Faculty. It is reused broadly by every Domain, but it does not understand what the data represents — it only stores and retrieves it.

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

## 19. 2026-09-04 — Rename PLAN_KEYS: one_year/one_month/this_week/this_hour/this_minute/right_now → year/month/week/hour/minute/now

**Alternatives considered:** keep the original names; rename only the broadest slot (`one_year`); make PLAN_KEYS dynamic/generated instead of a fixed tuple.
**Why this choice:** the old names mixed two different things under one vocabulary - literal/deictic time expressions (`one_year`, `this_week`, `right_now`) and the actual role each key plays: a plan-record time level, not a promise about the real span it covers. That mismatch became a concrete problem once a goal's own resolved duration could exceed a level's literal name - a 5-year goal's broadest relevant horizon was still called `one_year`. `year`/`month`/`week`/`hour`/`minute`/`now` name the levels themselves; the actual temporal semantics and concrete durations remain entirely `foundation/time`'s job (`resolve_duration()`/`describe_duration()`/`resolve_span()`), unchanged by this rename. `today` was left as-is - already a plain level name, not a literal or deictic expression needing correction. This also supersedes docs/06-development.md's 2026-08-26 entry, which kept `right_now`/`PLAN_KEYS` unchanged specifically because renaming them "would be a real migration for a purely cosmetic gain" - the motivation here is semantic correctness, not cosmetics, and the migration itself is now done (see Trade-off).
**Trade-off:** none identified - `_HORIZON_LENGTH_THRESHOLDS` and `broadest_relevant_horizon()`'s fill/null logic are unchanged in behavior, only in the strings they use. Existing `data/plans.json` records (saved under the old names) are remapped on load via `data_persistence._LEGACY_HORIZON_KEY_RENAMES`, so no stored plan content was lost or needs a manual migration step.
**Reversible?** Yes - `_LEGACY_HORIZON_KEY_RENAMES` could be reversed the same way it was added; no data was deleted, only remapped on read.

## 20. 2026-09-05 — Classify Math as a Faculty; refine decision #16's Faculty criterion to include fundamental reasoning domains

**Alternatives considered:** classify `backend/foundation/math.py` as Infrastructure (parallel to `data_persistence.py`'s "doesn't understand what the data represents" reasoning); leave it unclassified/informal until real cross-system reuse is demonstrated, per decision #16's literal wording; classify it as a Faculty now, on the grounds that it represents a fundamental reasoning domain rather than interpretation of ambiguous input.
**Why this choice:** decision #16 defined a Faculty as "a reusable capability for understanding or interpreting something," illustrated entirely through Time's role interpreting *ambiguous natural-language* temporal expressions ("this weekend" → a date). That framing left an open question decision #16 didn't need to answer at the time: is resolving ambiguous input the defining trait of a Faculty, or one example of a broader thing - a fundamental, independently-existing domain of reasoning the agent can operate within? Math clarifies this: `add`/`subtract`/`multiply`/`divide` don't interpret ambiguous text the way `phrase_matching.py` does - every input is already unambiguous - but Math represents the same kind of thing Temporal understanding does at a different layer: a basic domain of reasoning (quantitative, not temporal) the agent needs a deterministic, non-guessed capability for, the same "code decides, the model is told" principle Time already established. Math and Time are therefore both Faculties for the same underlying reason - fundamental reasoning domains the agent operates within - not because Math independently cleared decision #16's original "interprets ambiguous input" bar on its own terms.
**Why decision #16 isn't reversed, only refined:** its core three-way distinction - Faculty (understands/interprets) vs. Infrastructure (stores/transports, doesn't understand what the data represents) vs. Domain (subject matter operated on) - stands exactly as decided. What's added is that "understanding" is not limited to resolving ambiguous natural-language input; a fundamental, independently-existing reasoning domain (temporal, quantitative) also qualifies, whether or not any single primitive operation within it is itself ambiguous to resolve. `data_persistence.py` is still Infrastructure by the same original test - it still doesn't understand what the data it stores means. Unlike Time, Math has no paired Domain - nothing yet treats standalone quantities as first-class records the system operates on.
**Trade-off:** the Faculty bar is now somewhat less strict than decision #16's original wording literally implied - a future addition could try to claim Faculty status by analogy to "fundamental reasoning domain" without demonstrated reuse. Mitigated by decision #16's still-standing warning against creating a Faculty "purely as a conceptual category" - a candidate still has to be a genuine, independently-existing domain of reasoning, not just a plausible label, and this refinement doesn't relax that.
**Reversible?** Yes - a documentation/categorization decision, not a code dependency. `backend/foundation/math.py` stays a single flat file regardless (see docs/03-architecture.md § Math) - reclassifying it as Infrastructure later would mean editing docs, not code.

## 21. 2026-09-09 — Swap local model: llama3.1:8b → qwen3.5:9b (Q4_K_M), same runtime and boundary

**Alternatives considered:** keep `llama3.1:8b`; move to a hosted API model; switch to Qwen3.5-9B via a different local runtime (MLX) instead of staying on Ollama.
**Why this choice:** `qwen3.5:9b` is available directly from the Ollama library at a 4-bit (Q4_K_M) quantization (6.6GB) — no new runtime, no new model format handling, and no change to `backend/llm_client.py`'s `send_message()` interface, which already treats the concrete model as a one-line `MODEL` constant no caller depends on. MLX was considered (native to Apple Silicon) but rejected for now: Ollama already runs this exact model well on this machine (M3 Pro, 18GB), and Ollama's own MLX-backed tag (`qwen3.5:9b-mlx`, 8.9GB) is larger on disk/memory for no demonstrated benefit here — see `03-architecture.md` § Architectural principles, "Start simple." This is a development/testing choice, not a permanent architecture decision — the model is expected to change again.
**Trade-off:** `qwen3.5:9b` is a multimodal (text+image) model used here in text-only mode — unused capability, not a cost. Slightly larger on disk than `llama3.1:8b` (6.6GB vs 4.9GB); comparable memory headroom on this machine (see `04-current-state.md`).
**Reversible?** Yes, trivially — the model name is a single constant (`MODEL` in `backend/llm_client.py`); no caller of `send_message()` knows or needs to know which model is behind it.

## 22. 2026-09-14 — Ask a zoom's depth verdict in its own model call, separately from producing the level

**Alternatives considered:** one call deciding both whether a step needs breaking down and what its children are (the shape tried first); one call forbidden to decline, with stopping decided by code or left entirely to the user's choice of what to click; a deterministic rule (step count, duration, tree depth) deciding when to stop.
**Why this choice:** the one-call version was measured, not assumed, and it failed in a specific way — given a response schema where "no children" was valid, the model always took the cheap branch, returning empty for all five test steps including a 2-year "climb Mount Everest". Asked to do nothing but judge (`zoom.py`'s `is_too_coarse()`), the same model was unanimous and correct on five of seven cases; separately, when forbidden to stop, it decomposed well. It can do either job and collapses when one call has to do both. A deterministic rule was rejected on the precedent already set for step count (no entry of its own here — recorded in `04-current-state.md` § 8 and `calendar.py`'s own docstring): whether an Action can be projected from a step is a contextual judgment about resolution, not arithmetic, and the previous attempt to make this kind of call by formula (`step_count()`) had to be deleted for collapsing to a constant.
**Note on the apparent conflict:** `calendar.py` deliberately went the other way, folding two calls into one, because a separate structure call measurably destabilized the content call that *consumed* its output. That reasoning doesn't reach here — the verdict only gates whether the second call happens, and passes it nothing — so this is not a reversal of that decision. Both are recorded in `04-current-state.md` § 8 side by side for that reason.
**Trade-off:** two model calls per zoom instead of one, so every level costs roughly twice the latency; on the local model this is several seconds per click, which is also why `GET /api/tree` exists rather than rebuilding a tree on every page visit. The verdict is also least reliable at the deepest levels — "open the document and write the first paragraph", `planning-model.md` § Structural axis's own example of an Action, was called too coarse twice in three. Tolerable because no step is ever force-expanded: the cost is a zoom offered that shouldn't have been, not a wrong tree.
**Reversible?** Yes — `zoom_into()` is the only composition point, and collapsing back to one call means deleting `is_too_coarse()` and giving `children_of()`'s schema an empty-list branch again. Nothing persists either call's result on the Steps scratch tree (see `04-current-state.md` § 5); Goal `plan.progression` zoom-write is still unbuilt (#24).

## 23. 2026-09-17 — Global Ollama temperature 0.2 on every `send_message()` call

**Alternatives considered:** leave Ollama's default (~0.8); set temperature per caller (Voice higher, Decide/Fill/progression lower); omit the option and rely on prompts alone.
**Why this choice:** all model traffic already passes through `backend/llm_client.py`. Default sampling was producing inventiveness where the agent needs discipline (Voice claiming work already done; Decide ignoring an explicit "1 month"; fragile week-day JSON shapes). One low dial (`TEMPERATURE = 0.2`) for Voice, Describe, llm3, and Planning keeps the boundary honest — callers do not each invent a sampling policy. Same "one place to change the model" reasoning as decision #21's `MODEL` constant.
**Trade-off:** Voice may sound slightly flatter; if naturalness becomes a real product need, a second optional argument on `send_message()` can raise temperature for Voice only without scattering defaults elsewhere.
**Reversible?** Yes — change or remove `TEMPERATURE` in `client.py`; no persisted data depends on it.

## 24. 2026-09-17 — Shadow WHAT progression (`plan.progression`) beside legacy calendar steps; Active prefers it

**Alternatives considered:** keep calendar `plan.steps` / `PLAN_KEYS` as the only plan structure; replace them in one rewrite with recursive Steps; build progression only in the Steps workbench until later.
**Why this choice:** `planning-model.md` already treats Progression (WHAT) and Time (WHEN) as separate axes; runtime had mixed them (week candles as step count). Minting a shallow Step tree via `construct_progression.py` on Decide=PLAN, stored as `plan.progression`, lets Active show a real WHAT list without deleting legacy Fill/`generate_structure` yet. `to_planning_node()` prefers progression when present, else falls back to `plan.steps`. Calendar fill soft-fails without blocking progression. Matches the agreed "shadow first" migration — dual paths visible in `TODO.md` P3 until zoom writes into progression and legacy structure can be demoted.
**Trade-off:** two structures can exist on one record; replan still regenerates `PLAN_KEYS` and carries both trees forward unchanged. (Zoom-into-progression and user +/- beads were added the same day — see [[04-current-state]]; this entry's "zoom not built" line is stale.)
**Reversible?** Yes — stop writing `progression`, or ignore it in manifestation; old records without the field already fall back to legacy steps / surface only.

## 25. 2026-09-17 — Product direction: Project / mental-map workspace; user steers; Goal engine remains for now

**Decision:** Treat the product as a **Project** workspace whose job is a **mental map** (Start → waypoints → End), not an agent that finishes a plan or teaches. The **user steers** the line (chat + click; named beads via +/-); the agent **proposes** (one question or one concrete suggestion) and does not dump a syllabus. **Time is optional** for co-building and for progression zoom — not the gate and not the spine. Primary UI home is **Projects** (`/` → `projects.html`); Active stays as legacy. Persistence may keep `goal_id` / Goal records until a later rename; language and prompts migrate first.

**Date:** 2026-09-17

**Alternatives considered:** stay a Goal/execution planner that mints full progressions on PLAN; require timeframe before any structure; chat-only or click-only editing of the map; rename storage/`goal_id` in the same breath as the UI shell.

**Why this choice:** Live tests showed both failure modes of the old feel — agent dumps a middle, or interrogates forever — while the wanted experience was co-building a map of *the user's* landmarks (e.g. school, first project). Teaching and schedules can be outsourced; the app orients. A Projects shell and user +/- beads already express that; Decide/Fill/prompts still speak Goal and still auto-mint on PLAN — so the direction is settled here, and implementation is a staged migration (thin slice: prompts + UI copy first; `02-product` / IDs later). See `TODO.md` Active 23 / Queue 23 and [[04-current-state]] § 5.

**Trade-off:** dual vocabulary (Project UI, Goal engine) until migration catches up; auto-`construct_progression` on PLAN still fights "user steers" until that path is narrowed. Zoom children can still feel like worksheets — map-vs-teaching is a prompt/product rule, not fully enforced in code. Dual paths must stay **named** in root `TODO.md` § Parallel paths (anti-mess rule) so the base does not grow a second undocumented planner.

**Reversible?** Yes at the product layer — drop Projects, restore Active-as-home, re-emphasize timeframe gates — without deleting `plan.progression`. Storage rename is independent and can wait or never happen.

## 26. 2026-09-19 — Orient the codebase as visual / do / data (inventory first, no mass move)

**Decision:** Treat **visual / do / data** as the standing orientation for where new code belongs and how cleanup is judged. **Visual** = `app/ui/` (DOM, SVG, layout, page chrome). **Do** = `app/backend/` plus entry wiring (`server.py` / `cli.py`) — `backend/project/` (was `planning/`), `backend/agent/` (Voice, Describe, Node 3, manifestation), faculties, model boundary. **Data** = `backend/store/data_persistence.py` and `data/*.json` — store and load only.

**Date:** 2026-09-19

**Alternatives considered:** reorganize `project/engine/` into WHAT/WHEN packages immediately; invent new top-level packages outside `ui/` / `backend/` / `data`; keep organizing only by creation date or by Goal-era subfolders without stating the three buckets.

**Why this choice:** Top level already roughly matches the three buckets; the real muddle is **inside do**, especially `project/engine/` (Decide, calendar structure, WHAT progression, outline import, prompts in one folder). Naming the buckets stops “where does this go?” drift and supports later splits without a premature mass move mid-migration ([[05-decisions]] #25 / `TODO.md` Active 23). Inventory lives in [[04-current-state]] § 2.iv–v.

**Trade-off:** ~~`plan/` stays mixed on disk until a later move~~ — addressed 2026-09-20: WHAT in `panes/canvas/`; Decide/Fill in `engine/judgment/`; calendar dual in `engine/when/`; redundant `engine/plan/` folder removed. `projects.ts` remains a thick visual orchestrator for shell/chat (map visual gathered under `ui/src/map/` as of 2026-09-19) — chat split still flagged for a later round.

**Reversible?** Yes — the buckets are orientation, not a new runtime layer. Drop or refine the wording in docs without touching imports.

## 27. 2026-09-19 — Goal history on disk as JSONL (`plans.jsonl`)

**Decision:** Store goal/plan history as **JSON Lines** (`data/plans.jsonl` — one JSON object per line) instead of one JSON array (`data/plans.json`). `save_plan()` appends a line; in-place edits (`stamp_map_focus`) still rewrite the file atomically. A leftover `plans.json` array is migrated once on first load (written to `plans.jsonl`, original renamed `plans.json.bak`).

**Date:** 2026-09-19

**Alternatives considered:** keep the array file; split one file per goal; separate map storage from history; full event-sourcing (small events, not snapshots).

**Why this choice:** History had grown large enough that a single pretty-printed array was hard to open and costly to rewrite on every save. JSONL keeps the same snapshot semantics, makes append cheap, and stays greppable line-by-line. Per-goal files and map-out-of-band can wait.

**Trade-off:** Reads still load the whole history into memory (same as before). Append is not crash-atomic the way a full temp+rename rewrite is — a torn last line is possible if the process dies mid-append; rare for this single-user local MVP.

**Reversible?** Yes — convert JSONL back to a JSON array with a one-off script; call sites still go through `load_history()` / `save_plan()`.

## 28. 2026-09-19 — Vocabulary: Planning/Goal/map → Project/panes/engine

**Decision:** Treat older **Planning / Goal / map / plan-folder** wording as labels for today's **Project** capability and its layout: capability = Project (`backend/project/`); product unit = Project (wire: `project_id` / `/api/projects`, deprecated `goal_id` / `/api/goals` — #29); WHAT progression = canvas (`project/panes/canvas/`); Decide–Fill motor = engine (`project/engine/judgment/` + `when/`, not a capability; `planner.py` is a facade); UI home = Projects. Canonical table lives in [[04-current-state]] § Vocabulary. Dated history (`06-development`, older entries here) keeps old words on purpose.

**Date:** 2026-09-19

**Alternatives considered:** rewrite all historical docs to say Project; rename store/API in the same pass; leave dual vocabulary without a single map.

**Why this choice:** Knowledge about Decide, WHAT trees, and feedback still applies; only the capability *name* and folder layout changed. One Rosetta table stops re-asking "is Planning still the capability?" without a mass rewrite or a premature `goal_id` migration (#25 storage rename still open).

**Trade-off:** Readers still see "Goal" and `"planning"` in wire paths and llm3 until those renames land. Speculation in `concepts.md` may keep Goal/Plan language.

**Reversible?** Yes — update or drop the 04 table; no runtime dependency.

## 29. 2026-09-20 — Wire identity: `project_id` / `/api/projects`

**Decision:** Persist and expose project identity as **`project_id`**. Primary HTTP surface is **`/api/projects…`**. JSONL on load promotes legacy `goal_id` → `project_id` and rewrites the file when needed. Responses emit `project_id` and a deprecated `goal_id` mirror for one release. `/api/goals…` remains a thin alias to the same handlers. llm3 returns `"project"` (accepts legacy `"planning"`). Display-text field `goal` and most Python symbol names (`create_goal`, `ChatFocus.goal_id`, …) stay for a follow-up.

**Date:** 2026-09-20

**Alternatives considered:** big-bang rename of every Python symbol and the `goal` text field in the same pass; permanent dual keys on disk; skip API alias and break old bookmarks.

**Why this choice:** Phase A product feel was already settled (#25); wire rename was the parked Phase B in [[goal-to-project-migration]]. Compatibility layer lets UI and disk move together without a multi-day symbol sweep.

**Trade-off:** `/api/goals` and response `goal_id` must be removed in a later cleanup; internal Python still says “goal” in many places.

**Reversible?** Yes while the alias and JSONL normalize-on-load remain — restore writing `goal_id` and point UI at `/api/goals`.

## See also

- [[03-architecture]]
- [[06-development]]
- [[02-product]]
- [[goal-to-project-migration]]
