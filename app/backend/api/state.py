"""
Process-wide API state — free-conversation Session and Steps workbench tree.

Owned by backend.api (not agent/ or project/): HTTP adapters need a
place for request-spanning pointers that are not domain logic.
"""

# Contents
#  1. Free-conversation session
#      - session
#
#  2. Steps workbench tree
#      - tree / tree_duration / tree_zoomed
#      - mint_step_id()

from backend.agent.process_turn import Session
from backend.project.panes.canvas.bead import Step


# ============================================================
# 1. Free-conversation session
# ============================================================

session = Session()  # process-wide - /api/message only


# ============================================================
# 2. Steps workbench tree
# ============================================================

# In memory, one at a time, lost on restart, and deliberately NOT
# written through data_persistence: docs/planning-model.md §
# Decomposition / zoom leaves whether zoomed content is persisted
# explicitly undecided, so this page exists to look at the shape
# before that call is made. It is a workbench for the recursive Step
# model, not a second way to create a real Goal.
tree: Step | None = None
tree_duration = ""
# Which steps have actually been through zoom_into(). A step with no
# children means "not zoomed yet" or "zoomed, and the verdict was
# that an Action can already be projected from it" - opposite
# meanings for the UI, and nothing in Step itself distinguishes them.
tree_zoomed: set[str] = set()
_step_counter = 0


def mint_step_id() -> str:
    global _step_counter
    _step_counter += 1
    return f"s{_step_counter}"
