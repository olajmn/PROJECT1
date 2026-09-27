# UI

How the app's screen is laid out, how it should look, and where its code lives.

## 1. The columns

```text
┌──────────┬─────────────────┬──────────┐
│ sidebar  │     canvas      │   chat   │
└──────────┴─────────────────┴──────────┘
```

| Column | Job | Not its job |
|---|---|---|
| **Sidebar** | Accounts and their projects; create a project; Settings | The map; column widths |
| **Canvas** | The open project's nodes | Files on disk; old plan fields |
| **Chat** | The conversation, optionally about one node or one day of changes | The map itself |

The canvas is not a file browser: a future files view belongs in the
sidebar, not the middle column.

## 2. The canvas

```text
[#6]                     ← id (a header, not a node)
  └── [css setup]        ← project title (a header, not a node)
        │
        ○ node           ← top-level node (label + ⋯)
        │    · child
        │
        (+)
```

- **One vertical spine** under the title; children hang under their
  parent. Lines meet box edges, never cross labels.
- **Id and title** are headers in the same box style, but not nodes: no
  ⋯, add, or remove.
- **Each node** is its label and ⋯. Add here and Remove live in ⋯; the
  `+` under the spine stays visible.
- **One frame, no tabs.** − / + shows fewer or more levels. The scroll
  wheel zooms and dragging pans, vertically; double-click resets to an
  overview. Below ~20% zoom the view switches to **Line** (each bar is a
  node), above ~26% back to **Text**; the toolbar can pin either.
- **An empty project** opens at natural size with a short hint, not a
  zoomed-out empty frame.
- **Controls around the map** — Copy as ASCII, Paste structure, Add
  folder, Saved trees, Archive — sit in the bar below it, quieter than
  the map.

Not planned for now: free placement of nodes, panning outside the frame,
card-style nodes.

## 3. The look

- **Hierarchy first.** Sort what is loud, quiet, and hidden before any
  styling. If two things look equally loud, the hierarchy failed.

  | Loud | Quiet | Hidden until needed |
  |---|---|---|
  | Project title, selected node | `#N`, child nodes, lines | Add / Remove (in ⋯) |

- **Complexity is budgeted.** The canvas may be rich — the tree, menus,
  and lines are the product's own UI. Shell, sidebar, and chat stay calm.
  Add a signal only when it earns a place; prefer removing one.
- **Two base planes**, light and dark (Settings → General). All three
  columns share one background so later depth can read as layers.
- **Frosted depth is a direction, not built:** soft translucency that
  lets you sense what sits behind, without hurting readability.

## 4. Where the code lives

- **Mirror rule:** `app/ui/src/<area>/` ↔ `app/ui/css/<area>/`, same
  names on both sides — behavior in `src/`, look in `css/`. A new
  surface gets or extends a pair, not a dump into `style.css`.
- **Areas:** `shell/` (column widths, collapse, busy state — glue, not a
  parent), `panes/create/` (sidebar and accounts), `panes/canvas/`,
  `panes/chat/`, `settings/`.
- **Tokens:** shared look lives once in `css/tokens.css`. If it should
  look the same everywhere, change a token; don't add a colour in an
  area file.

## 5. Done when

- Changing a few tokens retints the whole UI.
- Naming an area lets you open its `src/` and `css/` folders at once.
- A stranger tells primary from secondary text at a glance.
- The map stays rich; everything around it stays calm.

## See also

- [[02-product]] — what the app can do
- [[03-architecture]] — how the UI talks to the backend
