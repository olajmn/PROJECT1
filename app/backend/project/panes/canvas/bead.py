"""
The Plan's structural axis: one recursive Step type, used at every
depth. Depth is data, not type - "Goal", "Step" and "substep" name
where a step sits in a tree, not what class it is. See
docs/planning-model.md § Structural axis, which elects "Step" as the
general term for exactly this, in place of the fixed Stage/Micro-step
levels earlier drafts used.

Pure shape and tree operations - no model call, no persistence. A
step is stored inside a plan record's own dict, so every field here
has to survive json.dumps().

Shadow-wired from generate_plan() as plan["progression"] (WHAT
tree beside legacy plan["steps"]). Active's to_planning_node()
prefers progression when present; zoom into that tree from Active
is not built yet. Legacy calendar/session records still use
calendar.py's two-level {"label", "microsteps"} shape.
"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field


@dataclass
class Step:
    """One position in a plan tree - see module docstring."""

    # Minted once and never reused, so a step can change without
    # becoming a different step. Display numbering ("1.", "i.") is
    # computed from sibling position at render time and deliberately
    # not stored here - see ui/src/map/tree.ts.
    id: str
    label: str
    children: list["Step"] = field(default_factory=list)

    # Absolute path when this bead was minted from a file or folder.
    # Absent on beads the user typed or pasted.
    path: str | None = None

    # Whether the children have to happen in order. A master's year 2
    # requires year 1; Everest's equipment does not. True matches how
    # today's flat step list already behaves.
    ordered: bool = True

    # Whether this step's claim is realized. Separate from which step
    # currently holds attention - that is one value per goal, not a
    # flag per step (see docs/planning-model.md § Completion).
    resolved: bool = False

    def add_child(self, step: "Step") -> None:
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
        default rather than requiring a migration - same tolerance
        data_persistence.py already applies to older records."""
        return cls(
            id=data["id"],
            label=data["label"],
            ordered=data.get("ordered", True),
            resolved=data.get("resolved", False),
            path=data.get("path") or None,
            children=[cls.from_dict(child) for child in data.get("children", [])],
        )


def from_nested_labels(entries: list[dict], mint_id: Callable[[], str]) -> list[Step]:
    """Build steps from a nested [{"label", "children": [...]}] list,
    recursing to whatever depth that list actually has rather than a
    fixed two.

    `mint_id` is passed in rather than generated here so that ids stay
    unique across a whole goal, not just within one call.
    """
    return [
        Step(
            id=mint_id(),
            label=entry["label"],
            children=from_nested_labels(entry.get("children", []), mint_id),
        )
        for entry in entries
    ]
