# 07 — Features

> See [[05-product]] for what the agent should/shouldn't do.

## Candidate list (from the core idea description)

The agent should potentially be able to:

- [ ] understand goals (natural language input)
- [ ] break goals down (multiple time horizons)
- [ ] prioritize
- [ ] create tasks
- [ ] track progress
- [ ] detect deviations
- [ ] replan
- [ ] adapt to the user's situation
- [ ] choose the right granularity
- [ ] communicate proactively
- [ ] reduce how much project-managing the user has to do themselves

**Don't build all of it.** This list is a menu, not a spec — pick what
proves the hypothesis in [[04-hypothesis]], defer the rest to
[[13-ideas-parking-lot]].

## Refined long-term capability list (2026-08-18)

More precise naming for the same idea, from a parallel ChatGPT
discussion — capabilities the agent could eventually have, explicitly
**not built simultaneously**:

- Goal interpretation
- Planning
- Replanning
- Task decomposition
- User interaction
- Memory
- Temporal awareness (see [[08-technical-architecture]])
- Information retrieval / aggregation (a *capability* the agent can call
  on, not the core product — e.g. weather, calendar, maps, resources —
  see [[13-ideas-parking-lot]])
- Personal knowledge base (RAG over user-supplied documents — see
  "Knowledge" room below, 2026-08-22)
- Proactive notifications
- Reflection
- Progress tracking

## Architecture framing: Program / Rooms / Sitemap (2026-08-21)

The user's own framing, borrowed from building architecture, for
thinking about what the agent actually is - kept here as the product
definition, and as the mental model to build from going forward.

**Program** (what the building is for):
> The agent should help a person go from a goal to a concrete plan.

**Rooms** (the functions the building needs - mapped to what already
exists in code):

| Room | What it is today |
|---|---|
| Goals | `goal` + `goal_id` (`backend/storage.py`) |
| Plans | the `plan` dict: `one_year` / `one_month` / `this_week` / `today` / `this_hour` / `this_minute` / `right_now` (widened to the full year-\>minute ladder 2026-08-22, was three rungs + `right_now` before) |
| Tasks | not yet its own room - see "right_now is a trigger, not a time variable" below |
| Time periods | `duration` + `resolve_duration()` (`backend/agent/distributed/timeperiod/resolve.py`) |
| Conversation | the You/Agent thread on each active goal (`_active_goal.html`) - can now also be the agent asking a clarifying question instead of stating a plan, when the goal as given is too vague (2026-08-22, see `backend/agent/specialized/plan.py`'s `generate_plan()`) |
| History | `get_history_for_goal()` / the `/history` log |
| Knowledge | not built yet - see "Knowledge (RAG over user documents)" below |

**Sitemap** (how the rooms connect):

```
user -> agent -> goals -> plans -> [year, month, week, day, hour, minute]
```

The time axis (year down to minute) is a pure *when* hierarchy - it
doesn't exist as real STORAGE structure yet (see
[[08-technical-architecture]] § Memory & Data Architecture's
folder-per-time-period idea, parked, not built) - `data/plans.json`
remains one flat file regardless. The `plan` dict itself, though, now
has every rung on the ladder (`one_year`/`one_month`/`this_week`/
`today`/`this_hour`/`this_minute`/`right_now`) as of 2026-08-22 - it
used to stop at `this_week` with nothing between it and `right_now`.

**`right_now` is a trigger, not a time variable.** It doesn't belong on
the same axis as year/month/week/day/hour/minute - those describe a
shrinking window of *when*; `right_now` is the *action* that fires once
the time hierarchy has resolved all the way down to the present
moment. Treating it as just the smallest time-horizon (as `PLAN_KEYS`
currently does, listing it alongside `one_year`/`one_month`/`this_week`
as if it were a peer) blurs two different things: a description of a
time window, versus the actual task to execute. This is "Tasks" as its
own room in the table above - not built yet as a distinct concept from
`right_now`, but this is the reasoning for why it should eventually be
one.

## Knowledge (RAG over user documents) (2026-08-22, sketched — not built)

Discussed while deciding whether the project needs SQL (see
[[12-decisions]]): the user wants the agent to eventually draw on a
personal library of supplied documents (e.g. text files with
documented science behind them) when reasoning about a goal or plan -
not just the model's own training, not a live internet search either.
This is a distinct capability from "Information retrieval /
aggregation" above (weather/calendar/maps - live *external* data) -
this is the user's *own*, offline, supplied material.

**Why this isn't a SQL problem.** The actual mechanism this needs is
called **RAG** (Retrieval-Augmented Generation): find the stored chunks
whose *meaning* is closest to the current goal/question, and hand those
to the model as grounding before it answers. "Closest in meaning" is
answered by comparing **embeddings** (text turned into a numeric
vector) via similarity, not by an exact-match SQL `WHERE` clause - a
fundamentally different retrieval mechanism, not a bigger version of
the goals/plans storage question.

**Sketched pipeline:**

```
text files  ->  chunked (a few paragraphs at a time)
            ->  each chunk embedded (Ollama, local - same model
                family already running for plan generation, no new
                dependency, no API key, no cost)
            ->  stored as (chunk text, vector) pairs
            ->  at plan/replan time: embed the goal/question, find the
                closest stored chunks, inject them into the prompt
                actually sent to the model (this is the "augmented"
                part - the model still generates the answer, just with
                real material in front of it instead of only its own
                training)
```

**Storage: start as flat as `data/plans.json` already is, not a vector
database.** At personal-library scale (hundreds of documents, low
thousands of chunks), comparing a query embedding against every stored
vector in a plain loop is fast enough - no index, no separate engine,
same "simplest thing that actually works" reasoning `backend/storage.py`
already follows for goals. A real vector store/index (e.g. sqlite-vec,
Chroma - still local, still no server, no cost) only earns its keep once
brute-force comparison is *felt* to be slow - same "revisit when it's a
real, felt problem" threshold [[08-technical-architecture]] § Memory &
Data Architecture already applies to folder-per-time-period storage.

**Explicitly not decided/built yet:** file format for the chunk+vector
store; how a chunk's source document is cited back to the user; how
retrieved chunks are woven into `plan.py`'s existing `SYSTEM_PROMPT`/
`REPLAN_SYSTEM_PROMPT` without crowding out the goal/history context
already sent; whether ingestion is a one-off manual script or an
ongoing "drop a file in a folder" flow. Needs its own conversation
before any code gets written.

## See also

- [[09-mvp]] — what's actually chosen for the MVP
