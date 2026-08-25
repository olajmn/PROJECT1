# architecture_mapper

A standalone script that reads a Python package's own source code
(`ast` module only - no execution, no third-party dependencies) and
generates a drawio architecture diagram from it: modules as nodes,
imports as edges, external dependencies (Flask, Ollama, ...) as their
own nodes.

## Why this lives outside `backend/`

This is deliberately **not** part of the agent - it imports nothing
from `backend`, and nothing in `backend` imports from here. It only
knows generic Python (files, functions, imports), never anything
project-specific (no "goal", no "plan", no Flask routes). That's what
makes it safe to lift out of this repo intact later and reuse as an
external capability/tool the agent itself could call on - see
[[13-ideas-parking-lot]] "Tools / APIs the agent can use" and
docs/05-decisions.md for why it was built now despite that not being
an MVP priority.

## What it does NOT do

It can only ever describe what's true **today**, straight from the
code - it has no way to know about `docs/03-architecture.md`'s
future/"VISION" components, since those aren't code yet.
`docs/08-architecture.drawio` (hand-maintained, NOW + VISION sections)
stays the source of truth for the full picture. This script's output is
a **cross-check against that NOW section**, not a replacement for it -
run it after a structural change and compare, rather than assuming the
two will ever be auto-synced.

## Usage

```bash
.venv/bin/python3 tools/architecture_mapper/generate_diagram.py backend \
    --out tools/architecture_mapper/output/architecture-auto.drawio
```

Open the output file at [diagrams.net](https://app.diagrams.net).

## How the layout works

A simplified version of the standard "Sugiyama" layered-graph-drawing
method (see the module docstring in `generate_diagram.py` for the full
step-by-step): modules are layered by longest import-path from an entry
point, ordered within each layer to reduce line crossings, and long
edges are split through small invisible waypoint nodes so a line never
has to cut through an unrelated box to reach its target - the exact
problem that made the hand-drawn version messy before this existed.

## Known limitations (not built yet)

- No Flask-route or class extraction - functions and imports only.
- Node ordering combines barycenter sweeps with a "transpose" cleanup
  pass (standard technique, Gansner et al. 1993), plus an alignment
  pass afterward that nudges each node toward its neighbors' x without
  changing the order (straightens jogs into lines without touching
  crossing count). All positioning (order + x) is generic - no
  project-specific layout rules.
- **Entry points are pinned to one shared row** (everything with an
  `if __name__ == "__main__":` block lands directly under User), so the
  diagram reads as "here are the N things you can run", not scattered
  by how deep each one sits in the import graph. Trade-off, measured on
  this codebase (2026-08-20): crossings went from 0 back up to 2 to buy
  that clarity - pinning removes the layering algorithm's freedom to
  place those nodes wherever is optimal. A same-layer ("lateral") edge
  between two pinned entry points (one importing another) is forced
  adjacent and docked corner-to-corner instead of top-to-bottom - see
  `Edge.lateral` and `_fix_lateral_order`.
- `input("...")` calls with a literal string prompt are shown on the
  User edge (e.g. `types: "What do you want to achieve?"`) - the one
  fully generic, framework-agnostic signal for "a human types here."
  Doesn't catch input arriving through a web framework's own request
  object (e.g. Flask's `request.form.get(...)`) - that would mean
  hardcoding knowledge of a specific framework, which this tool
  deliberately avoids (see "Why this lives outside backend/" above).
- Relative imports (`from .x import y`) are only handled in the simple
  same-package case this codebase actually uses; deeply nested relative
  imports aren't specifically tested.
