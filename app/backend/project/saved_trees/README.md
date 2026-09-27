# Saved trees

What a saved tree is, and what is true about it today. This is the
concept's own current state, like `../node/README.md` is for nodes:
when a change alters what a saved tree is or which rules apply to it,
update this file in the same change. Reasoning: `docs/05-decisions.md`
#54.

## What a saved tree is

A node and everything under it, kept as bare **structure** in the
account's library, so it can be inserted again under any node, in any
of that account's projects.

A saved tree is a snapshot, not a template and not a link. Inserting it
creates new, independent nodes; nothing stays linked in either
direction.

## What is kept, and what is not

`structure_of()` (`../node/node.py`) decides this:

| Kept | Dropped | Why dropped |
|---|---|---|
| `label` | `id` | Identity belongs to the original node (#52); every insert mints fresh ids |
| `ordered` | `resolved` | State, not structure; a copy starts unresolved |
| `children` | `path` | Points at one file on one disk |

## Record

Stored in `data/saved_trees.json` (`backend/storage/saved_trees_persistence.py`):

```json
{"id": "t3", "name": "Pasta Bolognese", "sim_user_id": 2,
 "saved_at": "…", "source": {"project_id": 36, "step_id": "p14"},
 "tree": {"label": "Pasta Bolognese", "ordered": true, "children": []}}
```

- `id` (`t1`, `t2`, …) is never reused: the file keeps an `id_hi`
  high-water mark, the same rule as node ids.
- `name` is the node's label at save time. Saving the same node twice
  makes two saved trees.
- `sim_user_id` is the owning account. Only that account's projects list
  or insert it.
- `source` records where it was saved from. Nothing links back to it.

## Flow

- **Save:** node ⋯ → "Save as tree" → `POST /api/projects/<id>/map/<step>/save-tree`
  → `save_tree_from_node()`.
- **List:** node ⋯ → "Insert saved tree…" opens a picker from
  `GET /api/projects/<id>/saved-trees` → `saved_trees_for()`, newest first.
- **Insert:** a picker row → `POST /api/projects/<id>/map/insert-tree`
  → `insert_saved_tree()` → `edit_map.import_map_outline()`, the same
  path as Paste. Fresh ids come from `_id_minter()`; a clashing top label
  is numbered (`Pasta Bolognese (2)`, #53). Event: `tree_inserted`.
- **Delete:** × on a picker row → `POST /api/saved-trees/<tid>/delete`.
  Removes it from the library only.

UI: `ui/src/panes/canvas/savedTrees/` (`saveTree.ts`, `insertTree.ts`),
styles in `ui/css/panes/canvas/savedTrees.css`.

## Limitations and open questions

- Insert is only under a node, not at the top level of the map.
- A saved tree can't be renamed, and there is no library page outside
  the picker.
- An unassigned project (`sim_user_id` null) shares one library with
  every other unassigned project.
- A cross-project identity for a saved or inserted tree (NFT direction)
  is not decided; `source` is only provenance.
