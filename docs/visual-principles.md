# Visual principles (draft)

Working direction for the Projects UI — not a pixel spec. Execution and folder mirror live in [[visual-reset]]. Tokens live in `app/ui/css/tokens.css`.

## 1. Hierarchy first

Good design starts by **sorting text** — literally and meta.

- **Literal:** title → body → muted meta → decorative chrome. If two things look equally loud, hierarchy failed.
- **Meta:** what the product treats as primary (map nodes, the question in chat) vs secondary (ordinals, “Imported…”, resize grips).

Blur, glass, and accent come **after** this sort is clear. Otherwise transparency just smears noise.

## 2. Frosted glass = depth, not decoration

Aim: layers that feel slightly open so you sense **contrast of what sits behind** (map behind chat, shell behind panels) — a frosted-glass *idea*, not a glassmorphism kit.

- Prefer soft translucency / shared stone grounds over heavy backdrop-filter everywhere (readability first).
- Glass must not fight type hierarchy or make map spines unreadable.
- Light / dark are the two *base planes* (token sets); frosted is optional depth on top of either. The three Projects columns (sidebar / canvas / chat) share one base fill (`--color-bg-workspace`) so frost can read as layering, not three painted slabs. No purple glow or multi-layer shadow stacks — keep ink-on-stone honesty ([[visual-reset]] Phase B). Toggle: Settings → General.

## 3. Visual complexity is budgeted

**Simple / clean / modern** here means *few competing signals*, not fewer capabilities.

| Surface | Complexity budget |
|---|---|
| **shell** | Low — glue only (columns, tabs, busy) |
| **sidebar** | Low–medium — list + Manager |
| **chat** | Low–medium — transcript rhythm; About frames ok |
| **map** (canvas) | **High allowed** — tree, menus, spines are the product’s unique UI; column roles + spine layout: [[surfaces]] |

Add chrome only when it earns a hierarchy slot. Prefer removing a signal over adding a style.

## 4. How we work

1. Name the hierarchy levels for the surface you’re touching (what is loud / quiet / invisible). Canvas sort is locked in [[surfaces]] § 4.
2. Change tokens or area CSS — same `src/<area>/` ↔ `css/<area>/` mirror.
3. If it should look the same everywhere → token. If only here → area file.
4. Screenshot; ask whether the *sort* got clearer, not whether it got “prettier.”

## 5. Done-ish when

- Changing a few tokens retints the shell without rewriting areas.
- A stranger can tell primary vs meta text in one glance.
- Map stays rich; chrome around it stays calm.
- Glass (when introduced) reveals structure behind, not mud.

*Draft — revise when frosted layers land for real.*
