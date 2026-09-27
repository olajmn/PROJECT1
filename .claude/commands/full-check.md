Run the full project verification routine, in order. Steps 1–4 are
mechanical; step 5 is a read-only review. Change nothing unless asked —
report, then offer fixes.

1. **Orient.** Read `docs/04-current-state.md` and `TODO.md` (Active,
   § Parallel paths). They say what is supposed to be true and what is
   already known, so known items are not reported as new.
2. **`project_check`**: `app/.venv/bin/python3 -m tools.project_check`
   from the project root — git status, whether `docs/04-current-state.md`
   is stale, the `app/backend/` tree, an import smoke test, pyflakes,
   stale code-path mentions, modules with no inbound import, and
   `docs_check.py` / `docs_lint.py`.
3. **Every test suite**: each `test_*.py` under `app/backend/` (find them
   with `find backend -name 'test_*.py'` from `app/`), run from `app/` as
   `.venv/bin/python -m backend.<path>.test_<name>`. Don't rely on a
   fixed list — new suites get added.
4. **UI type check**: `npx tsc --noEmit` from `app/ui/` (no output means
   no type errors; nothing is written to `ui/dist/`).
5. **Review** — look for what the scripts cannot see. Spot-check with
   grep and targeted reads; this is a sweep, not a full audit:
   - **Dead code:** the no-inbound-import modules from step 2; functions,
     exports, CSS classes, or API routes nothing calls or uses.
   - **Duplicates / parallel paths:** the same job done in two places
     (two helpers, two UI paths, two ways to save the same thing). One
     not listed in `TODO.md` § Parallel paths is a finding.
   - **Stale text:** comments, docstrings, or docs naming files,
     functions, sections, or behavior that no longer exist; tables in
     `docs/03-architecture.md`, `docs/04-current-state.md`, and
     `docs/ui.md` that no longer match the code.
   - **Leftovers:** planner-era names or fields in live code paths
     beyond those already listed in `docs/04-current-state.md` § 5 and
     `TODO.md`.

**Report** compactly:
- What is clean (one line per step).
- Findings, each with `file:line`, what it is, and a suggestion: fix now,
  add to `TODO.md`, or already known (say where). Skip docs_lint REVIEW
  hits already listed as legitimate in `TODO.md`.
- Don't dump raw output unless something is actually wrong; retry a
  failing test once before reporting it.

If `docs/04-current-state.md` is flagged stale and real code or
architecture changed since it was last touched (not just doc-only
edits), offer to bring it back in sync — don't silently skip it, but
don't rewrite it if nothing substantive changed.
