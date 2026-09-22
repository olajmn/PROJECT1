# Surfaces — column roles + canvas layout

Working note for the Projects shell: **what each column is for**, and
how the canvas should *read*. Not a pixel spec. Product loop:
[[02-product]]. Vocabulary and on-disk homes: [[04-current-state]]
§ Vocabulary. Look budget: [[visual-principles]].

## 1. Three columns today

```text
┌──────────┬─────────────────┬──────────┐
│ sidebar  │     canvas      │   chat   │
└──────────┴─────────────────┴──────────┘
```

| Column | Job | Not |
|---|---|---|
| **sidebar** | Which Project / id — Manager (remembered open; brand-only close), create entry, list | The WHAT tree |
| **canvas** | Mental map: `#N` → title → waypoints (`plan.progression`) | Disk files; Decide/Fill engine |
| **chat** | Agent under optional canvas focus (About frames) | The map itself |

**Code homes (today):**

- Canvas data / write paths: `backend/project/panes/canvas/`
- Canvas UI (name lag): `app/ui/src/map/` + `app/ui/css/map/`
- Sidebar: `app/ui/src/sidebar/` + `user/activeUser.ts`
- Chat: `app/ui/src/chat/` + Projects compose in `pages/projects.ts`
- Shell glue (resize, tabs, rail): `app/ui/src/shell/`

## 2. What canvas is not

- **Not a file browser.** A future “run this folder / work files” view
  belongs in the **sidebar**, not the middle column. Parked until that
  capability exists; do not smuggle disk trees into the canvas.
- **Not the engine.** Decide / Fill / calendar live under
  `project/engine/`. Canvas is the WHAT bead tree the user steers.

## 3. Today vs aimed expression

Same data (`plan.progression` beads). Different read on screen.

| | Expression |
|---|---|
| **Today** | `#id` → title → tree in `.map-frame`; −/+ grain; camera zoom |
| **Was** | Nested outline + `#N`/name as fake root — read as a file tree |

**One living frame** (no Fit/All tabs):
- **− / +** — grow or shrink *tree depth* (grain). Boxes keep natural
  size; overview re-fits in the frame after each step.
- **Camera** (`frame/camera.ts`) — wheel zoom anchored under the cursor
  **vertically** (spine stays on the left edge), drag pan **up/down**
  (clamped — no empty gap above the tree). **Furthest out** = whole
  *visible grain* in the frame; **closest in** = natural size (1×).
  Double-click empty → overview (re-picks a readable grain). Unpins so
  zoom may auto-pick Line again.
- **Text | Line** (`frame/chrome.ts` + `skeleton/` + `lines/paint.ts`) —
  view mode, separate from zoom limits. **≤ ~20% → Line**, **> ~26% →
  Text** (hysteresis between). Toolbar sets preference until the next
  zoom threshold. Same nest hierarchy; in Line each horizontal bar *is*
  the node (length = bead width).
- First open / overview picks a grain that still reads in the frame.

Free node placement / pan outside the frame stay **out**. Rename
`map/`→`canvas/` after expression settles. Layout: § 4.

## 4. Layout (locked design)

ASCII, not pixels. Implementation later against `src/map/` + `css/map/`
— behavior stays (select, +, ×, ⋯, paste); expression changes.

```text
[#6]                     ← header bead (id; not a tree node)
  └── [css setup]        ← header bead (title; not a tree node)
        │
        ○ waypoint       ← spine bead (+ ⋯)
        │    · child
        │
        (+)
```

### Rules

1. **Axis** — Top → bottom under the project title. One vertical trunk
   through the beads (indented under the title).
2. **Poles** — Wire **id** (`#N`) then **project title** as two header
   levels (same *box* language as beads, but **not** progression nodes:
   no ⋯ / add / remove). Tree hangs under the title. No literal “Start”
   / bottom “End” labels.
3. **Spine beads** — Root `plan.progression` children only on the trunk.
   Plain label + ⋯. Light square around label+tools.
4. **Depth** — Children nest **under** their parent (drop from box
   bottom, tick into child left edge). DOM indent and SVG nest share
   one step (`mapGeom`). Depth text is **muted** vs spine. v1 keeps
   expand-all.
5. **Connectors** — Strokes meet **box edges** only (never through
   labels). Title → trunk exits the title **bottom** at the nest X.
6. **Node anatomy**
   - Idle / selected: label + **⋯** in the bead box; selected gets one
     clear signal (accent underline / unit border).
   - **Add here** and **Remove** live inside ⋯ (not loose + / × on the
     box). Spine-level **+** under the tree stays visible (new waypoint
     on the line).
7. **Empty project** — `#N`, title, quiet gap + hint (“talk or + to
   place a waypoint”). Lands at **natural size (1×) in Text** — not a
   zoomed-out overview of empty space.
8. **Chrome outside spine** — Copy as ASCII / Paste below the map
   (secondary). Archive stays in the project topbar.

### Hierarchy sort

| Loud | Quiet | Invisible until needed |
|---|---|---|
| Project title, selected bead | `#N`, depth children, spines | Add / Remove (in ⋯) |

### Out of this design pass

- Multiple named Fit/All view tabs (folded into one frame + −/+)
- Free drag placement of nodes; pan outside `.map-frame`
- Cards / glass nodes
- File-folder sidebar
- Renaming `src/map/` → `canvas/` (after expression lands)

## 5. See also

- [[02-product]] — co-build loop
- [[04-current-state]] — what is true on disk now
- [[visual-principles]] — canvas/map may use a high complexity budget
- [[visual-reset]] — `src/` ↔ `css/` mirror
