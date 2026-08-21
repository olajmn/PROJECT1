# 11 — Experiments

> Tests of [[04-hypothesis]] and product assumptions.

## Template

**Hypothesis tested:**
**Setup:** (who, how many, how)
**Result:**
**Learning:**
**Consequence:** (what do we change based on this?)

## Log

### 2026-08-21 — Naive substring matching in the free-text outcome classifier gives false positives

**Hypothesis tested:** N/A - found while building `backend/outcome_classifier.py`,
before it shipped, not from a designed test.
**Setup:** Tried the initial (plain substring) phrase matcher directly against
realistic edge-case free text before wiring it into the UI - e.g. "I don't
know yet", "not right now".
**Result:** A naive `if phrase in text` check for the recognized word "no"
matched *inside* "not", "know", "now" - "I don't know yet" would be
classified toward a negative outcome purely because "no" appears as a
substring of "know", even though the sentence never actually says no.
**Learning:** The exact same shape of risk as two later findings the
same day: "I may go" nearly resolving to next May (`_matched_month_name()`),
and the reason `DEADLINE_RE` needed a tolerant regex instead of an exact
phrase list. Any short recognized word that's also a substring of a
common longer word breaks under plain text containment - a systematic
risk in this project's whole "recognize known phrases" approach, not a
one-off bug.
**Consequence:** Fixed before shipping, via word-boundary regex matching
(`_contains_phrase()`, `\b`-wrapped so a phrase only matches as a whole
word) - see [[12-decisions]]. Same fix shape reused later the same day
for month-name matching (requiring "in" before the month name). General
principle going forward: never trust substring containment alone for a
short recognized word.

### 2026-08-20 (latest) — Long replan chains drift toward trivial actions, confirmed under real (non-stress-test) usage

**Hypothesis tested:** Does the 2026-08-19 stress-test finding below (drift
under 8 rapid clicks in under a minute) also show up under genuinely paced
real usage - actual attempts and feedback spread over hours, not a
deliberate rapid-fire test?
**Setup:** Real usage, goal "send 4 work applications" (`goal_id` 11),
spanning 2026-08-19 19:49 to 2026-08-20 19:00 - 15 total replan rounds
over roughly a full day of ordinary (not deliberately adversarial)
interaction.
**Result:** `right_now` degraded steadily across the chain: "Research and
list 4 job openings that match my skills and experience" → "List 4 job
openings... from companies already researched" → "research one company
for 30 minutes" → "browse a single job opening website" for 15, then 5,
then 2 minutes → "Spend 30 seconds checking the news for a new job
opening" - the action in the LAST of all 15 records. Across the entire
chain, `right_now` never once mentioned actually sending an
application - the goal's own stated action.
**Learning:** Confirms the 2026-08-19 stress-test finding wasn't an
artifact of rapid-fire clicking - the identical degradation happens
under genuinely paced real usage too, just slower. `replan()` only ever
saw the immediately-previous plan, so each individual shrink looked
locally reasonable to the model in isolation, but nothing stopped the
chain from compounding indefinitely further away from the goal itself.
**Consequence:** Fixed 2026-08-21 (see [[12-decisions]]): `replan()` now
receives the goal's FULL history (every right_now + feedback pair,
oldest first) instead of just the previous plan, and
`REPLAN_SYSTEM_PROMPT` now explicitly says to only shrink `right_now`
the first time it isn't completed, then move toward the goal's actual
core action instead of shrinking again. Verified against a simulated
reproduction of this exact 13-replan chain after the fix - `right_now`
advanced toward sending an application instead of continuing to shrink.

### 2026-08-20 — Hallucinated a specific person ("a friend") never mentioned

**Hypothesis tested:** N/A - noticed during real usage, not a designed test.
**Setup:** Real usage, goal "start going to the gym" (`goal_id` 12), no
duration given. First plan's `right_now`: "Research and shortlist 3 gyms
in the area and make a list of their membership options and pricing."
User feedback: "did not complete the action" plus a note about timing -
no other person mentioned anywhere.
**Result:** The next `right_now` read "Schedule a short call with a
friend to ask for their gym recommendations" - inventing a specific
person ("a friend") the user never mentioned in the goal text or the
feedback.
**Learning:** Same category as the earlier "chapter 11" (2026-08-18) and
"German vocabulary" (2026-08-19) hallucinations - a small, plausible-
sounding, entirely fabricated specific, not an obviously-wrong answer,
which is exactly what makes this kind of failure risky: it reads as
reasonable advice unless you notice you never actually said that.
**Consequence:** No fix applied (same as the other hallucination
findings - see [[09-mvp]] § Important distinction) - logged as further
evidence of an already-known limitation, not a new one. Reinforces this
project's core distinction between "the mechanism working" (plan → save
→ display → replan all functioned correctly here) and "the output being
reliable" (the specific content wasn't grounded in anything the user
actually said).

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
