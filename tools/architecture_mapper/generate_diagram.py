"""
Generate a drawio architecture diagram directly from a Python codebase's
own source - no hand-maintained node list, so the diagram can never
silently drift from what the code actually does.

WHY THIS LIVES OUTSIDE backend/: this is deliberately a standalone,
generic tool - it only reads Python source with the `ast` module and
knows nothing about this specific project (not "goal", not "plan", not
Flask). That's what makes it safe to lift out of this repo later and
reuse as an external capability, per docs/05-decisions.md. It imports
nothing from `backend`, and `backend` imports nothing from here.

WHAT IT DOES NOT DO: it only ever describes what's true today (the
"NOW" section of an architecture diagram) - it cannot know about
`docs/03-architecture.md`'s future/"VISION" components, since
those don't exist as code yet. docs/08-architecture.drawio (hand-
maintained) stays the source of truth for the full NOW+VISION picture;
this script's output is a cross-check, not a replacement.

HOW IT WORKS (a simplified version of the standard "Sugiyama" layered
graph drawing method used by most auto-layout tools):
  1. Parse every .py file under the target package with `ast` - collect
     its top-level function names, whether it's directly runnable
     (`if __name__ == "__main__":`), and every import.
  2. Turn imports into a directed graph: edges point from the importer
     to the thing it imports - either another module in this same
     package, or an external dependency (anything not in Python's
     standard library, e.g. `flask`, `ollama`).
  3. Assign each node a "layer" (vertical position) by longest path from
     an entry point - a module nothing else imports lands in layer 0,
     and anything gets pushed one layer below whichever of its callers
     needs it lowest. This guarantees every real edge always points
     from a strictly higher layer to a strictly lower one, so it can
     always dock top-to-bottom - no same-row edges to route around.
  4. Order nodes within each layer with a few "barycenter" sweeps
     (average position of connected nodes in the neighboring layer) -
     the standard cheap trick for keeping visually-related nodes near
     each other and reducing line crossings, without solving the
     (NP-hard) crossing-minimization problem exactly.
  5. Any edge that has to skip more than one layer gets split into a
     chain of tiny invisible waypoint nodes, one per skipped layer -
     otherwise a long edge would need to cut straight through whatever
     real boxes happen to occupy the layers in between.
  6. Render everything as drawio XML.

Run from the project root (see ../README.md in this folder):
    python3 tools/architecture_mapper/generate_diagram.py backend \
        --out tools/architecture_mapper/output/architecture-auto.drawio
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Step 1: parse the codebase
# ---------------------------------------------------------------------------


@dataclass
class ModuleInfo:
    """Everything extracted from one .py file's own source."""

    dotted_path: str  # e.g. "devtools.app"
    file_path: Path
    display_name: str = ""  # e.g. "devtools/app.py" - for readable labels
    functions: list[str] = field(default_factory=list)
    is_entry_point: bool = False  # has `if __name__ == "__main__":`
    # Literal prompt text from any `input("...")` call found in the
    # module - the one fully generic, framework-agnostic signal for
    # "a human types something here" (see add_user_node). Not filled in
    # for a non-literal prompt (e.g. input(some_variable)) - there's
    # nothing honest to display without running the code.
    input_prompts: list[str] = field(default_factory=list)
    # (source_names) -> set of imported names, discovered while parsing
    # this module's own import statements. Keys are dotted paths for
    # internal targets, or bare top-level names for external packages.
    imports: dict[str, set[str]] = field(default_factory=dict)


def _has_main_block(tree: ast.Module) -> bool:
    """True if the module has `if __name__ == "__main__": ...` at top level."""
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        ):
            return True
    return False


def _stdlib_names() -> set[str]:
    """Names to treat as noise (not worth drawing as external nodes)."""
    # sys.stdlib_module_names exists on Python 3.10+; this project runs
    # on newer Python (see CONVENTIONS.md), so no fallback is needed.
    return set(sys.stdlib_module_names)


def parse_package(root: Path, package_name: str) -> dict[str, ModuleInfo]:
    """
    Walk every .py file under `root` and parse it into a ModuleInfo,
    keyed by its dotted module path (e.g. "devtools.app").
    """
    modules: dict[str, ModuleInfo] = {}
    stdlib = _stdlib_names()

    py_files = sorted(
        p
        for p in root.rglob("*.py")
        if "__pycache__" not in p.parts
    )

    for file_path in py_files:
        rel = file_path.relative_to(root.parent)
        dotted = ".".join(rel.with_suffix("").parts)
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        functions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        info = ModuleInfo(
            dotted_path=dotted,
            file_path=file_path,
            display_name=str(file_path.relative_to(root)),
            functions=functions,
            is_entry_point=_has_main_block(tree),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = node.module
                names = {alias.name for alias in node.names}
                if target == package_name or target.startswith(package_name + "."):
                    info.imports.setdefault(target, set()).update(names)
                elif target.split(".")[0] not in stdlib:
                    info.imports.setdefault(target.split(".")[0], set()).update(
                        {target}
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top == package_name:
                        info.imports.setdefault(alias.name, set()).add(alias.name)
                    elif top not in stdlib:
                        info.imports.setdefault(top, set()).add(top)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "input"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                info.input_prompts.append(node.args[0].value)

        modules[dotted] = info

    return _drop_inert_modules(modules)


def _drop_inert_modules(modules: dict[str, ModuleInfo]) -> dict[str, ModuleInfo]:
    """
    Drop modules that would draw as an empty, disconnected box - no
    functions, not directly runnable, imports nothing, and nothing else
    imports it either (in practice: empty `__init__.py` package markers).
    A module kept for any other reason (even a single function or a
    single import in either direction) is left alone.
    """
    imported_targets = {target for info in modules.values() for target in info.imports}
    inert = {
        dotted
        for dotted, info in modules.items()
        if not info.functions
        and not info.is_entry_point
        and not info.imports
        and dotted not in imported_targets
    }
    return {d: i for d, i in modules.items() if d not in inert}


# ---------------------------------------------------------------------------
# Step 2-3: build the dependency graph and assign layers
# ---------------------------------------------------------------------------


@dataclass
class Node:
    id: str
    label: str
    kind: str  # "module" | "external" | "waypoint"
    lines: int = 1  # visual line count, for sizing the box to fit its text


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    # True for an edge whose source and target share a layer (only
    # possible once entry points are pinned to one row - see
    # assign_layers's `pinned` param). Docked left-to-right instead of
    # top-to-bottom when rendered.
    lateral: bool = False


USER_ID = "__user__"


def add_user_node(
    modules: dict[str, ModuleInfo], nodes: dict[str, Node], edges: list[Edge]
) -> None:
    """
    Insert one synthetic "User" node at the very top of the graph, wired
    to every module this script found runnable directly
    (`is_entry_point` - has `if __name__ == "__main__":`).

    This is deliberately the one node NOT derived from `ast` parsing: a
    human typing a command or opening a browser doesn't exist anywhere
    in the source code, so there's nothing to detect - it has to be
    added by hand. Everything else in the diagram is discovered
    automatically; this is the one place a person decided what to draw.

    The edge label is the one exception that's still earned from code:
    if the module calls the builtin `input("...")` with a literal
    prompt string, that string is shown on the arrow - a real, textual
    "here's where a human actually types something" moment, not a
    guess. A module with no `input()` call gets an unlabeled edge
    instead of an invented one - e.g. devtools/app.py (Flask) takes
    typed input too, but through `request.form.get(...)`, not
    `input()`; detecting that generically would mean hardcoding
    knowledge of a specific web framework, which is exactly the kind of
    project-specific assumption this tool is built to avoid (see
    README.md). Mutates `nodes` and `edges` in place.
    """
    nodes[USER_ID] = Node(id=USER_ID, label="<b>User</b>", kind="user")
    for dotted, info in modules.items():
        if info.is_entry_point:
            label = (
                f'types: "{info.input_prompts[0]}"' if info.input_prompts else ""
            )
            edges.append(Edge(USER_ID, dotted, label))


def build_graph(
    modules: dict[str, ModuleInfo]
) -> tuple[dict[str, Node], list[Edge]]:
    """
    Turn parsed modules into graph nodes + edges. An edge always means
    "source imports/depends on target" - so target should end up drawn
    below source once layered.
    """
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    for dotted, info in modules.items():
        # html=1 is set on every style below, so labels use real <br>/<b>
        # tags instead of literal newlines - a bare "\n" inside an XML
        # attribute value gets normalized away to a space by any XML
        # parser (including drawio's own), which is what used to make
        # every function name run together on one line.
        label_lines = [f"<b>{info.display_name}</b>"]
        if info.is_entry_point:
            label_lines.append("<i>(runs directly: __main__)</i>")
        # A leading underscore is Python's own convention for "internal
        # helper, not meant to be called from outside this file" - dim
        # those so a reader's eye lands on the functions that actually
        # matter first, the same way skimming the source itself would.
        label_lines.extend(_style_function_name(fn) for fn in info.functions)
        nodes[dotted] = Node(
            id=dotted,
            label="<br>".join(label_lines),
            kind="module",
            lines=len(label_lines),
        )

    for dotted, info in modules.items():
        for target, names in info.imports.items():
            if target in modules:
                edges.append(Edge(dotted, target, _wrap_names(sorted(names))))
            else:
                # External dependency (e.g. "flask", "ollama") - not one
                # of our own modules. Give it one shared node per name
                # even if several modules import it.
                if target not in nodes:
                    nodes[target] = Node(id=target, label=f"<b>{target}</b>", kind="external")
                label = _wrap_names(sorted(n.split(".")[-1] for n in names))
                edges.append(Edge(dotted, target, label))

    return nodes, edges


def _style_function_name(name: str) -> str:
    """Dim a leading-underscore (internal helper) name; leave public ones plain."""
    if name.startswith("_"):
        return f'<span style="color:#6b8f6b;font-style:italic;">{name}</span>'
    return name


def _wrap_names(names: list[str], per_line: int = 3) -> str:
    """
    Join a list of names for an edge label, breaking every `per_line`
    items onto a new line instead of one dense comma-separated wall of
    text - easier to scan, especially once an edge represents 5+ names.
    """
    groups = [names[i : i + per_line] for i in range(0, len(names), per_line)]
    return "<br>".join(", ".join(g) for g in groups)


def assign_layers(
    nodes: dict[str, Node],
    edges: list[Edge],
    pinned: dict[str, int] | None = None,
) -> dict[str, int]:
    """
    Longest-path layering: a node's layer is one more than the deepest
    of whatever imports it. Modules nothing imports (real entry points)
    land in layer 0.

    `pinned` forces specific nodes to a fixed layer regardless of what
    their own predecessors would otherwise demand - used to put every
    entry point (everything a human can run directly) on the same row,
    so it visually reads as "these are N siblings" rather than however
    deep the import graph happens to bury each one. A downstream node's
    own layer is still computed normally from its predecessors' (now
    possibly pinned) layers, so nothing further down loses its ordering
    guarantee: layer(target) > layer(source) still holds for every edge
    EXCEPT one directly between two pinned nodes (e.g. one entry point
    importing another) - those become "lateral" edges, handled
    separately by insert_waypoints/order_layers/render_drawio.
    """
    pinned = pinned or {}
    predecessors: dict[str, list[str]] = {n: [] for n in nodes}
    for e in edges:
        predecessors[e.target].append(e.source)

    layer: dict[str, int] = {}
    visiting: set[str] = set()

    def layer_of(n: str) -> int:
        if n in layer:
            return layer[n]
        if n in pinned:
            layer[n] = pinned[n]
            return pinned[n]
        if n in visiting:
            # A real import cycle would loop forever here - fall back to
            # 0 rather than recursing infinitely. Not expected in a
            # codebase with no circular imports (Python would already
            # refuse to run it), but this keeps the tool safe either way.
            return 0
        visiting.add(n)
        preds = predecessors.get(n, [])
        result = 0 if not preds else 1 + max(layer_of(p) for p in preds)
        visiting.discard(n)
        layer[n] = result
        return result

    for n in nodes:
        layer_of(n)
    return layer


# ---------------------------------------------------------------------------
# Step 5: split long edges with waypoint nodes
# ---------------------------------------------------------------------------


def insert_waypoints(
    nodes: dict[str, Node], edges: list[Edge], layer: dict[str, int]
) -> list[Edge]:
    """
    Replace any edge that skips more than one layer with a chain through
    small invisible waypoint nodes, one per skipped layer, so the edge
    always docks to an adjacent layer - never cuts through a layer's
    real boxes. Mutates `nodes` and `layer` in place with the new
    waypoints; returns the replacement edge list.

    An edge between two pinned nodes in the *same* layer (span 0 - see
    assign_layers's `pinned`) needs no waypoints; it's marked `lateral`
    instead, so order_layers keeps source-before-target and
    render_drawio docks it left-to-right rather than top-to-bottom.
    """
    resolved: list[Edge] = []
    waypoint_count = 0

    for e in edges:
        span = layer[e.target] - layer[e.source]
        if span == 0:
            resolved.append(Edge(e.source, e.target, e.label, lateral=True))
            continue
        if span <= 1:
            resolved.append(e)
            continue

        prev = e.source
        for step in range(1, span):
            waypoint_count += 1
            wid = f"__wp{waypoint_count}"
            nodes[wid] = Node(id=wid, label="", kind="waypoint")
            layer[wid] = layer[e.source] + step
            # Label only the first segment, so the text doesn't repeat
            # down the whole chain.
            resolved.append(Edge(prev, wid, e.label if step == 1 else ""))
            prev = wid
        resolved.append(Edge(prev, e.target))

    return resolved


# ---------------------------------------------------------------------------
# Step 4: order nodes within each layer to reduce crossings
# ---------------------------------------------------------------------------


def order_layers(
    nodes: dict[str, Node], edges: list[Edge], layer: dict[str, int]
) -> dict[int, list[str]]:
    """
    Group nodes by layer, then order them in two stages (the standard
    combination, see Gansner et al. 1993):
      1. Barycenter sweeps - reorder each layer by the average position
         of the neighbors it's connected to above/below, pulling
         connected nodes into rough alignment.
      2. Transpose - swap adjacent nodes within a layer whenever that
         strictly reduces crossings, until no swap helps anymore (see
         `_transpose`). This is what catches what barycenter alone
         leaves behind, e.g. two unrelated waypoint chains sitting next
         to each other for no reason.
    Not an exact minimum - exact crossing minimization is NP-hard - but
    this combination is what real layout tools use precisely because it
    gets close for a modest graph like this one at negligible cost.
    """
    layers: dict[int, list[str]] = {}
    for n, l in layer.items():
        layers.setdefault(l, []).append(n)
    for l in layers:
        layers[l].sort()  # stable, deterministic starting order

    successors: dict[str, list[str]] = {n: [] for n in nodes}
    predecessors: dict[str, list[str]] = {n: [] for n in nodes}
    for e in edges:
        # Lateral edges connect two nodes in the *same* layer (see
        # insert_waypoints) - their order_of values aren't comparable to
        # a neighboring layer's (each layer indexes 0..len-1
        # independently), so they'd corrupt the barycenter average.
        # _fix_lateral_order enforces their source-before-target
        # ordering separately, after this cross-layer machinery runs.
        if e.lateral:
            continue
        successors[e.source].append(e.target)
        predecessors[e.target].append(e.source)

    def sweep(order_of: dict[str, int], neighbor_map: dict[str, list[str]]) -> None:
        def barycenter(n: str) -> float:
            neighbors = neighbor_map[n]
            if not neighbors:
                return order_of[n]  # no pull - keep current position
            return sum(order_of[m] for m in neighbors) / len(neighbors)

        for l in sorted(layers):
            layers[l].sort(key=barycenter)
            for i, n in enumerate(layers[l]):
                order_of[n] = i

    order_of = {n: i for l in layers.values() for i, n in enumerate(l)}
    for _ in range(2):
        sweep(order_of, predecessors)  # top-down pass
        sweep(order_of, successors)  # bottom-up pass

    _transpose(layers, order_of, predecessors, successors)

    # A lateral edge (one entry point importing another, both pinned to
    # the same row - see assign_layers) still has to read left-to-right
    # like every other arrow: source before target. Barycenter/transpose
    # optimize for crossings, not for this, so enforce it as a final
    # corrective pass.
    lateral_pairs = [(e.source, e.target) for e in edges if e.lateral]
    if lateral_pairs:
        _fix_lateral_order(layers, lateral_pairs)

    return layers


def _fix_lateral_order(
    layers: dict[int, list[str]], lateral_pairs: list[tuple[str, str]]
) -> None:
    """
    A lateral edge only draws as a clean straight connector if its
    target sits immediately next to its source in the row - otherwise
    (see the bug this replaced) the line cuts straight through whatever
    real box barycenter/transpose left sitting between them. That's the
    same problem waypoint nodes solve for edges that skip a layer,
    just sideways instead of down: force the adjacency directly, by
    pulling the target out of wherever it ended up and dropping it
    right after its source. A bounded, best-effort fix-up - fine for the
    handful of same-layer edges a pinned "all entry points on one row"
    layout produces, not a general constraint solver for many
    conflicting lateral edges in one row.
    """
    for _ in range(10):
        changed = False
        for row in layers.values():
            for u, v in lateral_pairs:
                if u in row and v in row:
                    i = row.index(u)
                    if row[i + 1 : i + 2] != [v]:
                        row.remove(v)
                        i = row.index(u)
                        row.insert(i + 1, v)
                        changed = True
        if not changed:
            break


def _crossings_for_pair(
    u: str, v: str, neighbor_pos: dict[str, int], neighbor_map: dict[str, list[str]]
) -> int:
    """
    Assuming u is placed immediately before v: how many crossings do
    their edges to one already-ordered neighboring layer create? An
    edge from u and an edge from v cross exactly when u's neighbor sits
    *after* v's neighbor in that layer - u is left of v here, so their
    lines have to swap sides on the way there.
    """
    pu = [neighbor_pos[a] for a in neighbor_map[u] if a in neighbor_pos]
    pv = [neighbor_pos[b] for b in neighbor_map[v] if b in neighbor_pos]
    return sum(1 for a in pu for b in pv if a > b)


def _transpose(
    layers: dict[int, list[str]],
    order_of: dict[str, int],
    predecessors: dict[str, list[str]],
    successors: dict[str, list[str]],
) -> None:
    """
    The standard cleanup pass after barycenter ordering (Gansner et al.'s
    "transpose" step): repeatedly try swapping each adjacent pair of
    nodes within a layer, keeping the swap only if it strictly reduces
    the number of edge crossings against both neighboring layers. Unlike
    barycenter (which nudges everything toward an average position),
    this directly targets the thing being minimized - crossings - so it
    catches cases barycenter alone leaves on the table, like two
    unrelated waypoint chains ending up side by side for no reason. Runs
    until a full pass makes no more improving swaps, or a small cap on
    iterations (a handful of modules converges almost immediately).
    """
    for _ in range(6):
        improved = False
        for l in sorted(layers):
            row = layers[l]
            above = layers.get(l - 1)
            below = layers.get(l + 1)
            for i in range(len(row) - 1):
                u, v = row[i], row[i + 1]
                before = 0
                after = 0
                if above:
                    above_pos = {n: idx for idx, n in enumerate(above)}
                    before += _crossings_for_pair(u, v, above_pos, predecessors)
                    after += _crossings_for_pair(v, u, above_pos, predecessors)
                if below:
                    below_pos = {n: idx for idx, n in enumerate(below)}
                    before += _crossings_for_pair(u, v, below_pos, successors)
                    after += _crossings_for_pair(v, u, below_pos, successors)
                if after < before:
                    row[i], row[i + 1] = v, u
                    order_of[u], order_of[v] = i + 1, i
                    improved = True
        if not improved:
            break


# ---------------------------------------------------------------------------
# Step 6: render as drawio XML
# ---------------------------------------------------------------------------

NODE_W = 300
LINE_H = 22  # generous per-line height at fontSize 11, so text never crowds the box
NODE_PAD = 26  # top+bottom padding inside a box, beyond its text
EXTERNAL_H = 60
WAYPOINT_SIZE = 14
LAYER_GAP = 170  # vertical breathing room between layers
COL_GAP = 70  # horizontal breathing room between sibling boxes
ROW_PAD = 40  # extra vertical padding added to every row, on top of its tallest box
MARGIN = 80

STYLE_MODULE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;align=left;verticalAlign=top;spacingLeft=8;spacingTop=8;fontSize=11;"
STYLE_EXTERNAL = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=12;"
STYLE_USER = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;"
STYLE_WAYPOINT = "ellipse;whiteSpace=wrap;html=1;fillColor=#999999;strokeColor=none;"
STYLE_EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=10;exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
# Same-layer ("lateral") edges dock left-to-right instead - see
# Edge.lateral, at the exact top corner (Y=0, no offset): text fills
# top-down from spacingTop=8/spacingLeft=8 with verticalAlign=top, so
# every other point along the left/right edge has some line of text
# right next to it on a box this densely packed - the corner, just
# outside where the text glyphs actually start, is the one spot that
# doesn't collide regardless of the box's height or line count.
STYLE_EDGE_LATERAL = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=10;exitX=1;exitY=0;entryX=0;entryY=0;"


def _node_size(node: Node) -> tuple[int, int]:
    """Box size for one node - tall enough for its own text, never cramped."""
    if node.kind == "waypoint":
        return WAYPOINT_SIZE, WAYPOINT_SIZE
    if node.kind in ("external", "user"):
        return NODE_W, EXTERNAL_H
    return NODE_W, NODE_PAD + node.lines * LINE_H


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _straighten(
    layers: dict[int, list[str]],
    positions: dict[str, tuple[float, float, float, float]],
    predecessors: dict[str, list[str]],
    successors: dict[str, list[str]],
) -> None:
    """
    Ordering (order_layers) already fixed *which* node sits where in its
    row - that's what controls crossings, and it's not touched here. All
    this does is nudge each node's x toward the average x of the
    neighbors it connects to, resolving any resulting overlap by
    shifting left-to-right within the row. That's what turns an
    avoidable diagonal jog into a straight line - the same kind of
    finishing pass real tools run after Sugiyama ordering (e.g.
    Brandes-Köpf), simplified. Mutates the x component of `positions`.
    """

    def center(n: str) -> float:
        x, _y, w, _h = positions[n]
        return x + w / 2

    def align(neighbor_map: dict[str, list[str]], reverse: bool) -> None:
        # Aligning to predecessors (they live one layer up) has to sweep
        # top-to-bottom so each node sees its predecessor's position
        # already updated *this* pass. Aligning to successors is the
        # mirror image - it has to sweep bottom-to-top, or every node
        # would align to its successor's stale, previous-pass position
        # instead of where that successor just moved to. Getting this
        # backwards is exactly what left single-predecessor/single-
        # successor waypoint chains a few pixels short of straight
        # instead of perfectly aligned.
        for l in sorted(layers, reverse=reverse):
            prev_right = None
            for n in layers[l]:
                x, y, w, h = positions[n]
                neighbors = [m for m in neighbor_map[n] if m in positions]
                desired_center = (
                    sum(center(m) for m in neighbors) / len(neighbors)
                    if neighbors
                    else center(n)
                )
                new_x = desired_center - w / 2
                if prev_right is not None:
                    new_x = max(new_x, prev_right + COL_GAP)
                positions[n] = (new_x, y, w, h)
                prev_right = new_x + w

    for _ in range(4):
        align(predecessors, reverse=False)
        align(successors, reverse=True)

    # Whichever way alignment shifted things, put the leftmost box back
    # at the margin rather than leaving an arbitrary gap on the left.
    min_x = min(x for x, _y, _w, _h in positions.values())
    if min_x != MARGIN:
        shift = MARGIN - min_x
        for n, (x, y, w, h) in positions.items():
            positions[n] = (x + shift, y, w, h)


def render_drawio(
    nodes: dict[str, Node],
    edges: list[Edge],
    layers: dict[int, list[str]],
    title: str,
) -> str:
    cells: list[str] = []
    positions: dict[str, tuple[float, float, float, float]] = {}

    # Two passes: first work out how tall each row needs to be (its
    # tallest box, since a module with many functions needs far more
    # room than a one-line external node), then place rows one under the
    # other using that real height - not a fixed guess - so a tall row
    # never overlaps the row below it.
    row_heights = {
        l: max((_node_size(nodes[n])[1] for n in row), default=EXTERNAL_H) + ROW_PAD
        for l, row in layers.items()
    }

    y = float(MARGIN + 60)
    for l in sorted(layers):
        row = layers[l]
        row_h = row_heights[l]
        x = float(MARGIN)
        for n in row:
            node = nodes[n]
            nw, nh = _node_size(node)
            # Top-aligned, not centered: every box in a row starts at
            # the same y regardless of its own height, so a lateral
            # edge's top-corner docking point (STYLE_EDGE_LATERAL)
            # lines up into one clean horizontal run instead of
            # zigzagging to match each box's differently-centered top.
            positions[n] = (x, y, nw, nh)
            x += nw + COL_GAP
        y += row_h + LAYER_GAP

    predecessors: dict[str, list[str]] = {n: [] for n in nodes}
    successors: dict[str, list[str]] = {n: [] for n in nodes}
    for e in edges:
        if e.lateral:
            continue  # same-row pull would fight the row's own left-to-right packing
        successors[e.source].append(e.target)
        predecessors[e.target].append(e.source)
    _straighten(layers, positions, predecessors, successors)

    for node_id, node in nodes.items():
        x, y, w, h = positions[node_id]
        if node.kind == "waypoint":
            style = STYLE_WAYPOINT
        elif node.kind == "external":
            style = STYLE_EXTERNAL
        elif node.kind == "user":
            style = STYLE_USER
        else:
            style = STYLE_MODULE
        safe_id = node_id.replace(".", "_").replace("/", "_")
        cells.append(
            f'<mxCell id="n_{safe_id}" value="{_escape(node.label)}" '
            f'style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" '
            f'height="{h:.0f}" as="geometry" /></mxCell>'
        )

    for i, e in enumerate(edges):
        s = e.source.replace(".", "_").replace("/", "_")
        t = e.target.replace(".", "_").replace("/", "_")
        style = STYLE_EDGE_LATERAL if e.lateral else STYLE_EDGE
        cells.append(
            f'<mxCell id="e_{i}" value="{_escape(e.label)}" style="{style}" '
            f'edge="1" parent="1" source="n_{s}" target="n_{t}">'
            f'<mxGeometry relative="1" as="geometry" /></mxCell>'
        )

    # Measured from the final (post-straightening) positions, not the
    # initial packed estimate - straightening can spread a row wider
    # than the tightest possible packing when it pulls nodes toward
    # neighbors that live further to the side.
    rightmost = max(x + w for x, _y, w, _h in positions.values())
    page_w = int(rightmost + MARGIN)
    page_h = int(y + MARGIN)  # `y` already advanced past the last row, see loop above

    body = "\n        ".join(cells)
    return f"""<mxfile host="app.diagrams.net">
  <diagram id="architecture-auto" name="Architecture (auto-generated)">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{page_w}" pageHeight="{page_h}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="title" value="{_escape(title)}" style="text;html=1;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="{MARGIN}" y="10" width="700" height="30" as="geometry" />
        </mxCell>
        <mxCell id="legend" value="{_escape('<b>Legend</b><br>Blue = User - the one node NOT found by parsing<br>code, added by hand (see script docstring)<br>Green = this codebase\'s own module<br>Orange = external dependency (import)<br>Small gray dot = routing waypoint only -<br>not a real component, just where a line<br>bends to reach a target 2+ layers away')}" style="rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fillColor=#f5f5f5;strokeColor=#666666;spacingLeft=8;spacingTop=6;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="{page_w - MARGIN - 320}" y="10" width="320" height="140" as="geometry" />
        </mxCell>
        {body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", type=Path, help="Path to the Python package to scan, e.g. backend"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("tools/architecture_mapper/output/architecture-auto.drawio"),
        help="Where to write the generated .drawio file",
    )
    parser.add_argument(
        "--package-name",
        default=None,
        help="Import prefix to treat as 'internal' (default: root's folder name)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    package_name = args.package_name or root.name

    modules = parse_package(root, package_name)
    nodes, edges = build_graph(modules)
    add_user_node(modules, nodes, edges)
    # Pin every entry point (everything a human can run directly) to the
    # same row, one below User - so it reads as "these are the N things
    # you can start", not scattered by how deep each one happens to sit
    # in the import graph. See assign_layers's docstring for the
    # lateral-edge trade-off this creates.
    pinned = {d: 1 for d, info in modules.items() if info.is_entry_point}
    layer = assign_layers(nodes, edges, pinned=pinned)
    edges = insert_waypoints(nodes, edges, layer)
    layers = order_layers(nodes, edges, layer)

    xml = render_drawio(
        nodes, edges, layers, title=f"{package_name} - auto-generated from source"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(xml, encoding="utf-8")
    print(f"Wrote {args.out} ({len(modules)} modules, {len(edges)} edges)")


if __name__ == "__main__":
    main()
