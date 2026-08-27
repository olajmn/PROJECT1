"""
Cheap, deterministic repository orientation - meant to run at the start
of a session (or before a claim about current state matters), so a
session doesn't have to trust its own memory or docs/04-current-state.md's
prose at face value. Reports observable facts: what's changed in git,
which files under the areas docs/04-current-state.md describes are
newer than that file itself, the actual backend/ tree, whether the
core modules still import, code-level hygiene (pyflakes, stale
backend/devtools path mentions, modules with no inbound import),
whether architecture_foundation/ (when present) still has its expected
shape, and the existing docs checkers' findings.

Interprets nothing about content or correctness. Whether a "newer file"
actually means docs/04-current-state.md is out of date, whether a tree
mismatch matters, whether a module with no inbound import is dead code
or a deliberate entry point, whether an architecture_foundation/
component's status or content is actually right, what to do about a
docs_check/docs_lint finding - all of that is a human/Claude judgment
call, not this script's. See ../COLLABORATION.md for how a session is
expected to use this output.

Reuses tools/docs_check.py, tools/docs_lint.py, and pyflakes (already
a project dependency, see requirements.txt) as sub-checks rather than
duplicating their logic - this script is repository-wide orientation,
a layer above them, not a third documentation checker or a code
analyzer in its own right:

    docs_lint.py     -> documentation style
    docs_check.py    -> documentation structural integrity
    pyflakes         -> unused imports, undefined names (code)
    project_check.py -> repository/project orientation (this file) -
                         also owns the small checks below that nothing
                         else covers: stale backend/devtools path
                         mentions in code comments, modules with no
                         detected inbound import, and whether
                         architecture_foundation/'s expected files
                         (when that directory exists at all) are still
                         there and non-empty
    tests            -> actual runtime behavior (not this file's job -
                         the import check below only confirms a module
                         doesn't raise on import, nothing more)

Run from the project root:
    .venv/bin/python3 -m tools.project_check

Exit code 0 if docs_check.py, docs_lint.py, pyflakes, the import smoke
test, and the architecture_foundation/ skeleton check (see
architecture_skeleton_check()) all pass; 1 if any of them found
something. The skeleton check only ever fails on a missing/emptied
expected file - never on whether a component's status or content is
right, which stays a human/Claude judgment call same as everything
else here. Every other section (git status, newer-than-04-current-
state, the backend/ tree, stale code-path mentions, modules with no
inbound import) is pure information and never affects the exit code -
none of them are "wrong" on their own; each one needs a human/Claude
to decide whether the thing it observed actually means anything.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = ROOT / "docs" / "04-current-state.md"
PYTHON = ROOT / ".venv" / "bin" / "python3"

# Only present on branches that actually carry the architecture skeleton
# (e.g. architecture-skeleton) - not main. See
# architecture_skeleton_check()'s docstring for why its absence is a
# silent skip, never a failure.
ARCHITECTURE_SKELETON = ROOT / "architecture_foundation"

# The five docs every architecture_foundation/ is expected to have at
# its root, regardless of which components currently exist under it -
# unlike component folders (checked dynamically, see
# architecture_skeleton_check()), this list is small and stable enough
# to name directly, same reasoning as SMOKE_IMPORT_MODULES above.
ARCHITECTURE_SKELETON_CORE_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "COMPONENT_MAP.md",
    "DECISIONS.md",
    "ROADMAP.md",
]

# Areas docs/04-current-state.md actually describes - not all of the
# repo, just the parts relevant to whether it might need a fresh look.
RELEVANT_AREAS = ["backend", "devtools", "docs"]

# Kept small and explicit rather than dynamically discovered - an
# orientation smoke test, not a dependency graph. Add a module here
# only if it's a real entry point worth confirming still imports.
SMOKE_IMPORT_MODULES = [
    "backend.planning.planner",
    "backend.goals.goal_logic.resolver",
    "backend.infrastructure.data_persistence",
    "devtools.app",
]


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess from the project root, return (exit code,
    combined stdout+stderr) - never raises; a failing sub-check is
    itself part of the report, not a crash. Only trailing whitespace
    is trimmed - `git status --porcelain`'s status columns are
    position-sensitive, so a leading-whitespace-eating `.strip()` on
    the combined output would corrupt its first line."""
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).rstrip()


def git_status() -> list[str]:
    """Every changed/untracked path from `git status --porcelain`,
    relative to the repo root - the raw fact, not an interpretation."""
    code, output = _run(["git", "status", "--porcelain"])
    if code != 0 or not output:
        return []
    # Porcelain format is "XY path" - the path starts after the two
    # status characters and a space.
    return [line[3:].strip() for line in output.splitlines()]


def files_newer_than_current_state() -> list[str]:
    """Every file under RELEVANT_AREAS whose mtime is newer than
    docs/04-current-state.md's own mtime. Purely observable - doesn't
    claim this means the doc is stale (a file can be touched without
    its meaning changing, and the reverse); that judgment is left to
    whoever reads the report. mtime, not `git log`, because this
    project's docs/ work is routinely uncommitted for a whole session
    at a time - `git log` sees nothing for a file that was never
    committed, mtime always does."""
    if not CURRENT_STATE.exists():
        return []
    reference = CURRENT_STATE.stat().st_mtime
    newer = []
    for area in RELEVANT_AREAS:
        area_path = ROOT / area
        if not area_path.exists():
            continue
        for path in area_path.rglob("*"):
            if not path.is_file() or path == CURRENT_STATE:
                continue
            if "__pycache__" in path.parts or ".obsidian" in path.parts:
                continue
            if path.stat().st_mtime > reference:
                newer.append(str(path.relative_to(ROOT)))
    return sorted(newer)


def backend_tree() -> list[str]:
    """The actual backend/ directory tree, one relative path per line -
    a plain fact to hold up against whatever docs/04-current-state.md's
    own "What exists" tree currently says. This script doesn't parse
    or diff the doc's prose tree itself - reading the doc and noticing
    a mismatch is exactly the kind of judgment call left to whoever
    reads this report, not something to automate here."""
    backend = ROOT / "backend"
    if not backend.exists():
        return []
    return sorted(
        str(p.relative_to(ROOT)) + "/"
        for p in backend.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    )


def import_smoke_test() -> list[str]:
    """Each module in SMOKE_IMPORT_MODULES, imported in its own
    subprocess (one bad import can't take down the rest) - failures
    only, since a clean import needs no report. Confirms importability,
    not behavior - see this file's own docstring for why that's the
    deliberate boundary."""
    failures = []
    for module in SMOKE_IMPORT_MODULES:
        code, output = _run([str(PYTHON), "-c", f"import {module}"])
        if code != 0:
            last_line = output.splitlines()[-1] if output else "failed, no output captured"
            failures.append(f"{module}: {last_line}")
    return failures


def run_tool(module: str) -> tuple[int, str]:
    """Run an existing tools/ script as a subprocess, reused as-is
    rather than reimplemented."""
    return _run([str(PYTHON), "-m", f"tools.{module}"])


def run_pyflakes() -> tuple[int, str]:
    """Run pyflakes (already a project dependency, see
    requirements.txt) against backend/ and devtools/ - unused imports
    and undefined names, reused as-is rather than reimplemented."""
    return _run([str(PYTHON), "-m", "pyflakes", "backend", "devtools"])


# A backend/... or devtools/...-looking .py path mentioned in a
# comment or docstring - the same shape of pattern tools/docs_check.py
# already uses for docs/<NN>-<name>.md references, aimed at code paths
# instead. docs_check.py stays scoped to documentation; this stays
# scoped to code, so the two don't overlap.
CODE_PATH_RE = re.compile(r"\b(?:backend|devtools)/[A-Za-z0-9_/().-]+\.py\b")


def stale_code_path_mentions() -> list[str]:
    """Every backend/... or devtools/...-looking .py path mentioned
    anywhere under backend/, devtools/, tools/ that doesn't resolve to
    a real file. Doesn't distinguish a genuine leftover reference from
    a docstring deliberately narrating "moved from X" as history - the
    same distinction every other check in this file leaves to whoever
    reads the report, per ../COLLABORATION.md."""
    stale = []
    for area in ("backend", "devtools", "tools"):
        area_path = ROOT / area
        if not area_path.exists():
            continue
        for path in sorted(area_path.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in CODE_PATH_RE.finditer(line):
                    referenced = match.group(0)
                    if not (ROOT / referenced).exists():
                        stale.append(f"{path.relative_to(ROOT)}:{line_number}: {referenced}")
    return stale


def modules_with_no_inbound_import() -> list[str]:
    """Every backend/ module (excluding __init__.py) that no other
    .py file under backend/, devtools/, or tools/ appears to mention
    by dotted path or bare filename. A plain text search, not real
    import-graph analysis - it only counts whether the name appears
    anywhere, nothing more. Many entries here are legitimate (a
    command-line entry point run directly rather than imported - see
    SMOKE_IMPORT_MODULES above for the ones already confirmed as
    exactly that); this function doesn't know the difference, it only
    reports the raw list."""
    py_files = [
        p
        for area in ("backend", "devtools", "tools")
        for p in (ROOT / area).rglob("*.py")
        if "__pycache__" not in p.parts
    ]
    contents = {p: p.read_text(encoding="utf-8", errors="replace") for p in py_files}
    backend_modules = [
        p
        for p in (ROOT / "backend").rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    ]

    orphans = []
    for module_path in backend_modules:
        dotted = ".".join(module_path.relative_to(ROOT).with_suffix("").parts)
        base = module_path.stem
        referenced = any(
            dotted in text or f"import {base}" in text or f".{base}" in text
            for other_path, text in contents.items()
            if other_path != module_path
        )
        if not referenced:
            orphans.append(str(module_path.relative_to(ROOT)))
    return sorted(orphans)


def architecture_skeleton_check() -> list[str] | None:
    """
    Structural sanity check for architecture_foundation/ (see that
    directory's own README.md) - not every branch has it, and that's
    not a problem this function reports: returns None if
    ARCHITECTURE_SKELETON doesn't exist at all, meaning "nothing to
    check here", distinct from an empty list, meaning "checked, found
    nothing wrong".

    Checks only that the skeleton's shape hasn't silently eroded -
    the five core docs (ARCHITECTURE_SKELETON_CORE_DOCS) exist and are
    non-empty, and every directory under architecture_foundation/, at
    any depth, has its own non-empty README.md. Component folders are
    discovered by walking the tree, not a hardcoded list - same
    reasoning backend_tree() already follows: the set of components is
    expected to change as the skeleton evolves, so nothing here should
    need updating just because a folder was added, renamed, or removed.

    Deliberately does not check: whether a component's status
    (CURRENT/NEXT/FUTURE/EXPLORATORY) is accurate, whether its content
    is correct or complete, or whether a component should exist at
    all - "does the structure exist" is an objective, checkable fact;
    "is the architecture right" is a human/Claude judgment call, the
    same boundary every other check in this file already respects.
    """
    if not ARCHITECTURE_SKELETON.exists():
        return None

    problems = []
    for doc_name in ARCHITECTURE_SKELETON_CORE_DOCS:
        path = ARCHITECTURE_SKELETON / doc_name
        if not path.exists():
            problems.append(f"missing core doc: {path.relative_to(ROOT)}")
        elif path.stat().st_size == 0:
            problems.append(f"empty core doc: {path.relative_to(ROOT)}")

    for dir_path in sorted(ARCHITECTURE_SKELETON.rglob("*")):
        if not dir_path.is_dir() or "__pycache__" in dir_path.parts:
            continue
        readme = dir_path / "README.md"
        if not readme.exists():
            problems.append(f"component folder missing README.md: {readme.relative_to(ROOT)}")
        elif readme.stat().st_size == 0:
            problems.append(f"empty README.md: {readme.relative_to(ROOT)}")

    return problems


def main() -> int:
    exit_code = 0

    print("=== git status ===")
    changed = git_status()
    if changed:
        for path in changed:
            print(f"  {path}")
    else:
        print("  clean")

    print()
    print("=== files newer than docs/04-current-state.md ===")
    newer = files_newer_than_current_state()
    if newer:
        for path in newer:
            print(f"  {path}")
        print()
        print("  (observed fact only - whether this means")
        print("  docs/04-current-state.md needs a fresh look is a")
        print("  judgment call, not this script's.)")
    else:
        print("  none - docs/04-current-state.md is the most recently")
        print("  touched file among the areas it describes")

    print()
    print("=== backend/ tree (compare against docs/04-current-state.md § What exists) ===")
    for line in backend_tree():
        print(f"  {line}")

    print()
    print("=== import smoke test ===")
    failures = import_smoke_test()
    if failures:
        for failure in failures:
            print(f"  FAILED: {failure}")
        exit_code = 1
    else:
        print("  all modules import cleanly")

    print()
    print("=== pyflakes (backend/, devtools/) ===")
    code, output = run_pyflakes()
    print(output if output else "  no issues found")
    if code != 0:
        exit_code = 1

    print()
    print("=== stale backend/devtools .py path mentions ===")
    stale_paths = stale_code_path_mentions()
    if stale_paths:
        for line in stale_paths:
            print(f"  {line}")
        print()
        print("  (observed fact only - a dated docstring narrating a")
        print("  past move is expected to show up here too; whether a")
        print("  given hit is a leftover bug or intentional history is")
        print("  a judgment call, not this script's.)")
    else:
        print("  none")

    print()
    print("=== backend/ modules with no detected inbound import ===")
    orphans = modules_with_no_inbound_import()
    if orphans:
        for path in orphans:
            print(f"  {path}")
        print()
        print("  (observed fact only - a module can legitimately have")
        print("  no inbound import because it's a command-line entry")
        print("  point (see SMOKE_IMPORT_MODULES above) rather than")
        print("  dead code; that judgment is not this script's.)")
    else:
        print("  none")

    print()
    print("=== architecture_foundation/ skeleton check ===")
    skeleton_problems = architecture_skeleton_check()
    if skeleton_problems is None:
        print("  architecture_foundation/ not present on this branch - skipping")
    elif skeleton_problems:
        for problem in skeleton_problems:
            print(f"  {problem}")
        exit_code = 1
    else:
        print("  all core docs and component READMEs present")

    print()
    print("=== tools/docs_check.py ===")
    code, output = run_tool("docs_check")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    print()
    print("=== tools/docs_lint.py ===")
    code, output = run_tool("docs_lint")
    print(output if output else "  (no output)")
    if code != 0:
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
