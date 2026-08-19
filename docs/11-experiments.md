# 11 — Experiments

> Tests of [[04-hypothesis]] and product assumptions.

## Template

**Hypothesis tested:**
**Setup:** (who, how many, how)
**Result:**
**Learning:**
**Consequence:** (what do we change based on this?)

## Log

### 2026-08-19 — Long replan chains drift away from the original goal

**Hypothesis tested:** Does the replan loop stay anchored to the original
goal over many consecutive "not done" cycles, or does it drift?
**Setup:** Real usage by the project owner via `backend/devtools/app.py`.
Goal: "take a shower" (duration "1 hour"). Pressed "No" 8 times in a
row, in rapid succession (well under a minute total - a stress test,
not paced real-world usage), then "Yes" twice with a corrective note.
**Result:** The `right_now` action drifted steadily away from showering:
"go to the shower area" → "get the shower cleaner" → "find the remote
control to turn on the bathroom light" → "get out of bed" → "get
dressed" → "put on socks" → `null`. The user had to type "no i'm gonna
take a shower" to redirect it; even then the final response returned
`right_now: null`.
**Learning:** Not an isolated hallucination (like the earlier "chapter
11" or "German vocabulary" findings) - systematic drift over repeated
replan() calls. Confirms a known, previously-flagged architecture gap:
`replan()` only receives the immediately-previous plan, not the full
history or a reinforced original goal, so small deviations compound
over iterations. **Important caveat, discussed with the assistant
afterward:** 8 rapid "No" clicks with no real attempt in between is a
stress test, not representative of normal use (try the action for
real, then give feedback, likely once a day) - severity under normal
pacing is untested. The "Goal complete" button (built earlier the same
day) is an available escape hatch once a chain drifts.
**Consequence:** Logged as a known limitation of long replan chains
specifically, not of the core loop itself (which held up fine over 1-3
rounds throughout the rest of tonight's testing). Consider, before
further building: reinforcing the original goal text more strongly on
every replan() call, not just the previous plan. Revisit after testing
under normal (non-stress-test) pacing over several real days.

### 2026-08-19 — Goal identity is exact-text matching, not semantic

**Hypothesis tested:** N/A - incidental finding while building the
board feature ([[10-development]]).
**Setup:** Real usage: goal typed as "take shower" in one session, "take
a shower" (one extra word) in a later session, same real intent.
**Result:** `storage.get_board()` groups records by exact `goal` string
match - the two counted as two separate goals on the board, not one
continuing goal.
**Learning:** There is currently no concept of "this is the same goal"
beyond byte-for-byte text equality. A minor wording change (which
happens naturally in real use) fragments what should be one continuous
thread.
**Consequence:** Not fixed yet - noted as a real limitation. Fixing it
well (fuzzy/semantic matching, or an explicit goal ID the user
confirms) is more than a one-line change; revisit if it causes real
confusion during multi-day testing, rather than fixing preemptively.

### 2026-08-19 — Norwegian goal text causes severe, reproducible hallucination

**Hypothesis tested:** Does `llama3.1:8b` handle a goal written in Norwegian
as reliably as one written in English?
**Setup:** `generate_plan()` called directly (bypassing the UI) with the
same goal in both languages: `"lage mat"` (+ duration `"i løpet av
kvelden"`) vs. `"make food"` (+ duration `"during the evening"`).
Repeated 3 times for the Norwegian phrasing to check reproducibility.
**Result:** All 3 Norwegian calls produced answers unrelated to cooking -
two of them invented "German" content from nowhere ("Learn 10 new German
vocabulary words", "German dishes... start with Spätzle"), one
suggested "Translate 'lage mat'..." instead of an actual action. The
English phrasing of the *identical* goal, on the same call, produced a
sensible, grounded answer ("Check what ingredients are available in the
pantry and fridge"). Confirmed unrelated to the duration-resolution
feature built earlier the same day - `_resolve_duration()` correctly
computed "kveld" → 17:00-23:00 in every case regardless of the plan
quality.
**Learning:** This is a more severe reliability failure than the
"chapter 11" hallucination (2026-08-18 below) - there, one detail was
invented; here, the *entire* response was disconnected from the actual
goal, consistently, only when the input was Norwegian. `llama3.1:8b`'s
multilingual handling appears to be a real, reproducible weak point,
not an occasional fluke.
**Consequence:** User decision: write goals in English going forward
(see [[12-decisions]]) rather than switch LLM backend yet - keeps
testing free/local while sidestepping the specific failure mode found.
Revisit the Ollama-vs-Claude decision if English-only turns out to be
too much friction, or if similar failures show up in English too.

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
