# Architecture Foundation

This directory is the **architectural foundation / next-generation structure**
for the personal AI agent - a map of what a complete version of the agent
needs, not an implementation of it.

It exists alongside, not instead of, the **prototype / existing
implementation** in `backend/` and `frontend/`. Nothing there is touched,
moved, or migrated by anything in this directory. The prototype remains the
only thing that actually runs.

## What this is

- A folder per system responsibility, each holding a short `README.md`
  explaining what it represents, its current status, and its boundary with
  its neighbors.
- Almost entirely placeholders. No production code, no advanced logic, no
  dependencies. A handful of folders reference the prototype's existing,
  working code as the reference implementation for that responsibility -
  that reference is not copied here.

## What this is not

- Not a rewrite. Not a migration. Not a second implementation running
  alongside the first.
- Not a claim that everything here will be built. Most of it is explicitly
  marked `FUTURE` or `EXPLORATORY` - see each folder's `README.md` and
  `ROADMAP.md` below.
- Not a place for technologies (a neural network, a vector database,
  embeddings, RAG) to become folders of their own. Those are mechanisms a
  component might use later - see `COMPONENT_MAP.md` for where each one
  would actually plug in, and `ARCHITECTURE.md` for why they're deliberately
  not modeled as components.

## How to read this directory

1. **`ARCHITECTURE.md`** - the reasoning: what the components are, why they're
   split the way they are, and the data flow that connects them.
2. **`COMPONENT_MAP.md`** - the reference table: every component, its status,
   what it owns, and its relationship to its neighbors.
3. **`DECISIONS.md`** - what's actually been decided vs. what's current fact,
   exploratory, future, or genuinely unknown. Read this before assuming
   anything here is settled.
4. **`ROADMAP.md`** - sequencing: current, next, later, exploratory. What to
   actually pick up first.
5. Each component's own `README.md` for the specific detail on that one
   responsibility.

## Relationship to the prototype

The prototype (`backend/`, `frontend/`) already proves several of these
components work in practice: Vision, Goal, Plan, Action, Feedback, temporal
understanding (a Faculty), and persistence. Where that's true, the relevant
`README.md` here says so explicitly and points at the prototype file as the
reference - this skeleton doesn't re-explain or duplicate working code, it
places it correctly on the map.

The eventual next step, once this map is agreed, is to go through it
component by component and decide, for each one: **keep, move, rewrite, or
discard** the corresponding prototype code. That decision is explicitly not
made here - see `DECISIONS.md`.
