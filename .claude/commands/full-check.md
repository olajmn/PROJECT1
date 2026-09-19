Run the full project verification routine, in order:

1. `app/.venv/bin/python3 -m tools.project_check` (run from the project root) — reports git status, whether `docs/04-current-state.md` is stale, the `app/backend/` tree, an import smoke test, pyflakes, stale code-path mentions, orphan modules, and wraps `docs_check.py`/`docs_lint.py`.
2. The full test suite, each run from `app/`, with `app/.venv/bin/python`:
   - `-m backend.foundation.test_math`
   - `-m backend.foundation.time.test_time`
   - `-m backend.store.test_data_persistence`
   - `-m backend.project.panes.chat.feedback.test_feedback_parser`
   - `-m backend.project.engine.plan.test_planner` (live-model calls - if this fails, re-run it once before treating it as a real finding; this project has repeatedly observed transient local-model shape failures that resolve on a bare retry)

After both: report a compact summary - what's clean, and call out anything that isn't (a real stale-path/orphan finding, a docs_lint REVIEW hit not already known-legitimate, a test failure that persists on retry, `docs/04-current-state.md` staleness). Don't dump the full raw output unless something is actually wrong.

If `docs/04-current-state.md` is flagged stale and real code/architecture changed since it was last touched (not just doc-only edits), offer to bring it back in sync as part of this check, the same way earlier passes this session did - don't silently skip it, but don't rewrite it if nothing substantive actually changed.
