# TODO

Not a duplicate of `docs/04-current-state.md` - that file is the full,
factual account of what's true now, including known bugs/gaps and the
reasoning behind each. This file only tracks which of those are
actually being worked on (**Active**), a numbered catalog of
everything still open (**Queue**), and a **Parallel paths** table of
dual/redundant code — so scope and active pairs stay visible at a
glance.

Done / removed Stage-3 and old-plan items are **not** kept here;
their history lives in `docs/04-current-state.md` and
`docs/05-decisions.md`. An item moves from Queue to Active only when
deliberately chosen as next.

## Active

**34. Status panel, after the draft** (Step) —
polish after real use: removed-node names in "Recent map work",
wording, pinning facts said in chat. Dead `isolateRange` caller.
[[05-decisions]] #37; § 4.

**36. Isolate all LLM talk in one place** (Step, after 34) —
anything that prompts or calls a model (`model_input/`, `llm_client`,
Suggest prompts in `call_suggest`, …) should be one swappable module
on/off — SoT + Status stay the core; chat is a thin edge. Not a big
rewrite now; park until Status polish is clearer. § —

~~**35. Project SoT: current + event log**~~ — done 2026-09-26
([[05-decisions]] #41): `data/projects/{id}/current.json` +
`events.jsonl`; map/chat read current; Status/Logs read events;
legacy `{id}.jsonl` migrates on load. No replay engine in v1.

## Queue

Each item: kind (**Bug** / **Step** / **Question**) and impact tier
(**1** wrong today → **4** large new domain; **Untiered** = design
only). Numbers are stable ids, not rank. Detail stays in `docs/04`
unless noted.

### Tier 1

21. **Week/day calendar baseline** (Step, parked) — Time can still
    compute `week_windows()` / `day_windows()`, but nothing in the
    product calls them since project calendar fill was removed. Only
    relevant if time returns to the map (year face, ambient timeline).
    § 5. Related to 17, 27.

### Tier 2

12. **Decomposition / zoom** (Step) — map is user-steered
    (`plan.progression`); + / × / Paste / Add folder / Suggest /
    chat-suggest under a selected node write it. Still open: naming a
    node in chat without selecting it first, and remaining data-shape
    questions in [[planning-model.md]]. § 5, § 7, § 9.
26. **Id has no rename** (Step) — create and delete exist; no way to
    change an id's label after creation. § 1.i.
29. **Default project names are decided in the UI** (Step) — "New
    project N" lives in `defaultNames.ts`; move into `create_project()`
    when the name is empty so other clients share it. § 1.i.
30. **No written API reference** (Step) — short overview of each
    `/api/...` address. `docs/02-product.md` § 5.

### Tier 4

9. **A second capability** (Step) — agent can only do Project today.
   Design in `docs/03-architecture.md`. § 7.
10. **Memory domain** (Step) — not built. § 7, § 9.
11. **Knowledge / RAG** (Step) — not built. § 7.
13. **Acting** (Step) — no external action. § 7.
14. **Continuity / proactivity** (Step) — no scheduler / background
    behavior. § 7. Related to 17.
25. **2D box-diagram import** (Step) — paste today is indentation /
    outline only (`text_to_tree.py`); true 2D box diagrams need a
    different path (likely schema-constrained model read). § —

### Untiered

17. **Practices have no shape** (Question) — recurring open-ended
    commitments ("10 push-ups a day") fit no current axis. `docs/concepts.md`
    § 4.ix.
27. **What counts as a session / visit** (Question) — if the agent
    should understand time-with-the-user, build on `created_at` in
    project history / Logs, not server starts. § 5.
33. **Talk only sees the map's labels** (Question) — model gets labels
    + focus path, not file contents / notes behind a node. [[05-decisions]]
    #33.

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified. Detail:
`docs/04-current-state.md` § 5.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 21 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; map does not read leftover `plan.steps` |
| P3 | `plan.progression` vs legacy `plan.steps` | Leftover on disk only | Screen draws `progression` only; older records may still carry `steps` |
