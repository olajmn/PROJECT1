# Node

What a project node is, and what is true about it today. This is the
node's own current state: when a change here alters what a node is, how
it is identified, or which rules apply to it, update this file in the
same change. Project-wide state lives in `docs/04-current-state.md`;
the reasoning behind each rule lives in `docs/05-decisions.md`.

Not to be confused with the pipeline Nodes (Node 1 Interface, Node 2
Parser, Node 3 Decision) in `docs/03-architecture.md`. Those are system
responsibilities; a project node is one position in a project's tree.

## What a node is

One position in a project's tree, with a parent and children. The same
shape is used at every depth: depth is where a node sits, not what kind
of node it is. Canvas draws
nodes and chat talks about them; neither owns the shape. `node.py`
(`Step`) defines it, with no model call and no persistence.

## Fields

| Field | Meaning | Status |
|---|---|---|
| `id` | Identity (see below) | Used everywhere a node is found or referenced |
| `label` | Human-readable name | Shown on the map, in Copy as ASCII, and to the model |
| `children` | Ordered child nodes | Used |
| `path` | Absolute path, only on nodes minted from a file or folder | Set by folder import |
| `ordered` | Whether the children have to happen in order | Stored and copied by saved trees; drives no behavior yet |
| `resolved` | Whether the node's claim is realized | Stored, not read anywhere yet |

Display numbering (`1.`, `i.`) is computed from sibling position at
render time and is never stored.

## Identity: id, label, name path

Three different things (`docs/05-decisions.md` #52):

- **`id`** is the identity. Every backend write finds a node by id
  (`_find_step`, `remove_map_node`, `parent_id`), the UI selects by id,
  and chat turns about a node store `focus_step_id`.
- **`label`** is an attribute people use to describe the node. Two nodes
  may share a label.
- **Name path** (`Parent / Child`) is an addressing mechanism: `/add`
  and `/select` resolve it to an id (`id_at_path` in
  `panes/chat/commands/node_path.py`, first match per level).

To see ids: Talk `/id` with a node selected replies with its id and
path; with none selected it switches the map between showing ids and
labels (display only — `ui/src/panes/canvas/idView.ts`).

## Rules

- **Ids are never reused within a project.** Ids are `p1`, `p2`, …,
  minted by `_id_minter()` in `panes/canvas/edit_map.py`, which keeps a
  high-water mark in `plan["node_id_hi"]`. A removed node's id stays
  retired, because events and chat focus can still refer to it.
- **Ids are unique per project only.** `p12` exists in many projects. An
  identity across projects would need a separate global id.
- **Sibling labels stay unique**, as an addressing and readability rule,
  not an identity rule. A user-written clash (+, paste, folder, `/add`,
  `Step.add_child`) is numbered: `Taco`, `Taco (2)`, `Taco (3)`
  (`unique_sibling_label()`, `docs/05-decisions.md` #53). A
  model-suggested child that repeats a sibling is dropped instead.

## Where nodes live

Stored as plain dicts under `plan.progression.steps` in
`data/projects/{id}/current.json`, with `plan.node_id_hi` beside them.
Read them with `steps_of(record)` in `node.py`, the one place that
knows where they sit on a record; all writes go through
`panes/canvas/edit_map.py`. `tree_as_text.py` turns a tree into
indented labels for the model.

## Related and open

- Saved trees (`../saved_trees/`, `docs/05-decisions.md` #54) copy a
  node's structure without its identity. `structure_of()` in `node.py`
  decides what counts as structure:

  | Kept | Dropped | Why dropped |
  |---|---|---|
  | `label` | `id` | Identity belongs to the original node; each insert mints fresh ids |
  | `ordered` | `resolved` | State, not structure; a copy starts unresolved |
  | `children` | `path` | Points at one file on one disk |

  A saved tree is a snapshot, not a link: inserted nodes and the saved
  tree never affect each other.
- What `ordered` and `resolved` will drive is not decided.
