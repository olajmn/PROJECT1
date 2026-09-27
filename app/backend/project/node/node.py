"""
One project node: the recursive Step shape at every depth of the
family tree (parent/child). The atom the rest of the system builds from.

Depth is data, not type — where a step sits in the tree, not what
class it is (project/node/README.md).

Pure shape — no model call, no persistence. Stored inside
plan.progression; leftover plan.steps is not read here. Canvas/chat
are faces of nodes; they do not own the shape.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field


@dataclass
class Step:
    """One position in the project's node tree."""

    # Minted once and never reused, so a step can change without
    # becoming a different step. Display numbering ("1.", "i.") is
    # computed from sibling position at render time and deliberately
    # not stored here.
    id: str
    label: str
    children: list["Step"] = field(default_factory=list)

    # Absolute path when this node was minted from a file or folder.
    # Absent on nodes the user typed or pasted.
    path: str | None = None

    # Whether the children have to happen in order.
    ordered: bool = True

    # Whether this step's claim is realized.
    resolved: bool = False

    def add_child(self, step: "Step") -> None:
        step.label = unique_sibling_label(self.children, step.label)
        self.children.append(step)

    def walk(self) -> Iterator["Step"]:
        """Every step in this subtree, depth-first, self first."""
        yield self
        for child in self.children:
            yield from child.walk()

    def find(self, step_id: str) -> "Step | None":
        return next((step for step in self.walk() if step.id == step_id), None)

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "label": self.label,
            "ordered": self.ordered,
            "resolved": self.resolved,
            "children": [child.to_dict() for child in self.children],
        }
        if self.path:
            data["path"] = self.path
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        """A missing `ordered`/`resolved`/`children` reads as its
        default rather than requiring a migration."""
        return cls(
            id=data["id"],
            label=data["label"],
            ordered=data.get("ordered", True),
            resolved=data.get("resolved", False),
            path=data.get("path") or None,
            children=[cls.from_dict(child) for child in data.get("children", [])],
        )


def steps_of(record: dict) -> list:
    """The top-level nodes stored on a project record
    (`plan.progression.steps`), or [] when there are none or the shape
    is unexpected. The one place that knows where nodes sit on a record."""
    plan = record.get("plan")
    progression = plan.get("progression") if isinstance(plan, dict) else None
    steps = progression.get("steps") if isinstance(progression, dict) else None
    return steps if isinstance(steps, list) else []


def sibling_label_clash(siblings: list, label: str) -> str | None:
    """If a sibling already uses this label (same level), return an
    error string; else None. Accepts Step objects or dict steps."""
    wanted = (label or "").strip()
    if not wanted:
        return None
    for sib in siblings or []:
        if isinstance(sib, Step):
            existing = (sib.label or "").strip()
        elif isinstance(sib, dict):
            existing = (sib.get("label") or "").strip()
        else:
            continue
        if existing == wanted:
            return f'A sibling already named "{wanted}".'
    return None


_NUMBERED = re.compile(r"^(.*\S) \((\d+)\)$")


def unique_sibling_label(siblings: list, label: str) -> str:
    """`label`, or `label (2)`, `label (3)`, … — the first form no
    sibling at this level already uses. Accepts Step objects or dict
    steps.

    Identity is the id (docs/05-decisions.md #52); unique sibling labels
    only keep name paths (`/add`, `/select`) unambiguous and let people
    and the model tell siblings apart. So a clash is resolved, not
    refused. A label that already ends in ` (N)` counts on from N.
    """
    wanted = (label or "").strip()
    if not wanted or not sibling_label_clash(siblings, wanted):
        return wanted
    numbered = _NUMBERED.match(wanted)
    base, n = (numbered.group(1), int(numbered.group(2))) if numbered else (wanted, 1)
    while True:
        n += 1
        candidate = f"{base} ({n})"
        if not sibling_label_clash(siblings, candidate):
            return candidate


def structure_of(step: dict) -> dict:
    """A stored step dict as bare structure: label, order, children.

    Deliberately drops `id` (identity stays with the original node —
    docs/05-decisions.md #52), `resolved` (state, not structure; a copy
    starts unresolved), and `path` (points at one file on one disk).
    The result is the same {"label", "children"} forest shape Paste
    imports, plus `ordered`.
    """
    return {
        "label": str(step.get("label") or ""),
        "ordered": bool(step.get("ordered", True)),
        "children": [
            structure_of(child)
            for child in step.get("children") or []
            if isinstance(child, dict)
        ],
    }


def from_labels(labels: list[str], mint_id: Callable[[], str]) -> list[Step]:
    """One flat level of nodes from label strings."""
    return [Step(id=mint_id(), label=label) for label in labels]


def from_nested_labels(entries: list[dict], mint_id: Callable[[], str]) -> list[Step]:
    """Build steps from a nested [{"label", "children": [...]}] list,
    recursing to whatever depth that list actually has. Copies `path`
    when present (folder walk) and `ordered` when present (saved tree).

    `mint_id` is passed in so ids stay unique across a whole project,
    not just within one call.
    """
    steps: list[Step] = []
    for entry in entries:
        path = entry.get("path")
        steps.append(
            Step(
                id=mint_id(),
                label=entry["label"],
                path=path if isinstance(path, str) and path else None,
                ordered=bool(entry.get("ordered", True)),
                children=from_nested_labels(entry.get("children", []), mint_id),
            )
        )
    return steps
