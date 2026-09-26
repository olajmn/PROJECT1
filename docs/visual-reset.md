# Visual reset — plan + mirrored UI folders

Principles (hierarchy, glass, complexity budget): [[visual-principles]].

Checkpoint before this work: `architecture-v5` @ `e9c6bda` (full-check clean).

**Goal:** One deliberate visual identity over the existing product shell — not a new architecture. CSS and TS share the same map so “where does this live?” has one answer.

## Rule of the mirror

```text
app/ui/src/<area>/…     ↔     app/ui/css/<area>/…
```

- Same area names on both sides.
- Behavior/DOM in `src/`; look in `css/`.
- A new visual surface gets (or extends) a pair — not a one-sided dump into `style.css` or an unrelated module.
- Shared tokens live once: `css/tokens.css` (imported by everything). No parallel “theme” in TS except tiny product strings (`ACCOUNTS_BRAND`, etc.).

## Target tree

```text
app/ui/
├── style.css                 # import order only (tokens → base → areas)
├── pages/                    # static HTML entry points (unchanged role)
├── dist/                     # tsc output
├── css/
│   ├── tokens.css            # colors, type, space, radius — the identity
│   ├── base.css              # reset / body defaults using tokens
│   ├── shell/                # columns, tabs, busy/spinner, layout chrome
│   ├── panes/create/         # sidebar rail + Accounts panel (was Manager/id)
│   ├── map/                  # progression canvas (today: canvas/ + map TS)
│   ├── chat/                 # thread, compose, About-frames
│   └── pages/
│       └── settings/         # chrome + register (+ thin tab sheets if needed)
└── src/
    ├── api.ts / types.ts
    ├── user/                 # active id — pairs with sidebar brand conceptually
    ├── shell/
    ├── sidebar/
    ├── map/
    ├── chat/
    └── pages/
        ├── projects.ts       # orchestrator only
        └── settings/
            ├── register/     # shared register (blocks + paint)
            ├── general/
            ├── directory/
            └── logs/
```

**Mental picture:** three product columns are **siblings**; `shell` is the glue (resize, tabs, busy), not their parent folder.

```text
                    ┌─────────────────────────────────────┐
                    │              shell                   │
                    │   (layout · resize · tabs · busy)    │
                    └─────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   ┌─────────────┐            ┌──────────────┐            ┌─────────────┐
   │   sidebar   │            │     map      │            │    chat     │
   │  Manager    │            │  progression │            │   thread    │
   │  ids/list   │            │              │            │             │
   └─────────────┘            └──────────────┘            └─────────────┘

app/ui/
├── css/tokens.css
├── style.css
├── css/                     ↔  src/
│   ├── shell/               ↔  shell/
│   ├── sidebar/             ↔  sidebar/
│   ├── map/                 ↔  map/
│   ├── chat/                ↔  chat/
│   └── pages/settings/      ↔  pages/settings/
```

## Cleanup while aligning (do as move/rename, not redesign)

Fold or delete leftovers so the mirror stays honest:

| Today (noise) | Target |
|---|---|
| `css/canvas/` vs `src/map/` | **done** — both are `map/` |
| `css/create/`, `css/vision/`, `src/vision/` | gone / N/A in current tree |
| `src/settings/` duplicate of `src/pages/settings/` | **done** — only `pages/settings/` |
| chat rules split oddly | all under `css/chat/` + `src/chat/` |
| width rules | stay in `src/shell/columnResize.ts`; look in `css/shell/` |

## Execution order

### Phase A — Structure (before look changes)
1. Add `css/tokens.css` with placeholder tokens (current colors copied in — no visual change yet).
2. Rename/move CSS+TS to the target mirror (map, drop dead vision/create paths, settings only under `pages/`).
3. Wire `style.css` imports to the new paths; `tsc` + smoke Projects + Settings.

### Phase B — Identity (visual reset)
1. Decide 5 tokens: background, text, muted, accent (sparse), font pair + spacing steps.
2. Strip card/shadow/pill noise; one button language.
3. Apply by area in order: `shell` → `sidebar` → `map` → `chat` → `pages/settings`.
4. Screenshot before/after each area.

### Phase C — Done when
- Changing 2–3 tokens retints the whole UI.
- You can name an area and open the matching `src/` + `css/` folders without hunting.
- No new features in the same commits as token/skin moves.

## Out of scope
- Backend, wire names (`sim_user_id`, `project_id`), register *data* shape.
- Inventing micro-files for ceremony; same-concern fixes stay in the file that owns them.

## How to work on one area (e.g. chat)

1. Open the pair: `src/chat/` + `css/chat/` (same for sidebar / map / shell).
2. Area-only styles stay in that `css/<area>/` folder — use `var(--…)` from tokens.
3. If it should look the same everywhere → add/change a token in `css/tokens.css` (or `base.css`), don’t invent a new hex in the area file.
4. **Not** “three files per pane”. Map may grow more files because the tree UI is uniquely heavy; chat can stay small.

```text
general:  tokens.css + base.css
area:     css/<name>/  ↔  src/<name>/
heaviest: css/map/ + src/map/   (nodes, menus, spines)
```
