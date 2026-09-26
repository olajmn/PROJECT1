"""
One project node: the recursive Step shape at every depth of the
family tree (parent/child). The atom the rest of the system builds from.

Depth is data, not type — where a step sits in the tree, not what
class it is. See docs/planning-model.md § Structural axis.

Pure shape — no model call, no persistence. Stored inside
plan.progression; leftover plan.steps is not read here. Canvas/chat
are faces of nodes; they do not own the shape.
"""

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
        clash = sibling_label_clash(self.children, step.label)
        if clash:
            raise ValueError(clash)
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


def from_labels(labels: list[str], mint_id: Callable[[], str]) -> list[Step]:
    """One flat level of nodes from label strings."""
    return [Step(id=mint_id(), label=label) for label in labels]


def from_nested_labels(entries: list[dict], mint_id: Callable[[], str]) -> list[Step]:
    """Build steps from a nested [{"label", "children": [...]}] list,
    recursing to whatever depth that list actually has. Copies `path`
    when present (folder walk).

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
                children=from_nested_labels(entry.get("children", []), mint_id),
            )
        )
    return steps
