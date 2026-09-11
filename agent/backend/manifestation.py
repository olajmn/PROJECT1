"""
UI Manifestation (docs/v4-migration-decision.md) - turning a Planning result
into what a UI can show, without Planning knowing anything about UI
concerns and without the UI knowing Planning's own field names
(PLAN_KEYS, step_status, current_step, ...). This is the first
concrete home for the "UI manifestation" layer docs/v4-migration-decision.md
names but leaves unspecified - filled in only as far as Planning's
actual result shape requires, not as a general framework.

Two translations, deliberately kept separate and both pure functions
of an already-existing Planning record - neither calls Planning, an
LLM, or persistence:

- surface_text(): the ONE plain-text sentence LLM1 is allowed to see
  and relay conversationally (see backend/llm1/interface.py). Same
  precedence current/'s _active_goal/_conversation.html chat thread
  already uses.
- to_planning_node(): an OPTIONAL, generic {id, label, status,
  children} tree - used only when the record actually has a step list
  to show. Most records don't (most goals never resolve to a real
  duration span - see planner.generate_plan()), and that's fine; a
  caller gets None and falls back to surface_text() alone. This is NOT
  a domain model and NOT the final shape of "Point"/"Path" from
  earlier conceptual work - it is only as much structure as today's
  actual `plan.steps`/`step_status`/`current_step` already carry. Each
  top-level step's own microsteps (see plan_structure.py) become its
  `children`, one level deep only - `current_step`/`step_status` still
  track completion at the top-level-step granularity only, not per
  microstep; a microstep node's own `status` is always "open".
"""

from backend.foundation.time import step_plan as _step_plan


def surface_text(record: dict) -> str:
    """The one plain-text summary of a Planning record - see module
    docstring."""
    plan = record.get("plan", {})
    if plan.get("clarification"):
        return plan["clarification"]
    if plan.get("suggested_action"):
        return plan["suggested_action"]
    if plan.get("suggested_duration"):
        return f"No timeframe was given for this - would {plan['suggested_duration']} work?"
    if plan.get("pending_duration_question"):
        return plan["pending_duration_question"]
    if plan.get("now"):
        return plan["now"]
    return "(no next action came back - give feedback again, or mark complete)"


def to_planning_node(record: dict) -> dict | None:
    """{"id", "label", "status", "children"} rooted at the Goal, with
    one child per step - or None if this record has no step list to
    show (see module docstring). `status` is one of "open"/"current"/
    "done" per step, and "current"/"done" for the root goal node.

    Reuses foundation.time.step_plan() (already verified, unchanged)
    for step time-labels when a frozen duration exists, rather than
    re-deriving anything about time here - this module only shapes
    Planning's existing output for display, it does not compute
    anything new."""
    plan = record.get("plan", {})
    steps = plan.get("steps")
    if not steps:
        return None

    current_index = record.get("current_step", 0)
    status_list = record.get("step_status")
    if not status_list or len(status_list) != len(steps):
        status_list = ["open"] * len(steps)

    # step_plan() only slices time and reads each entry as a plain
    # label to embed as "text" - it has no reason to know about
    # microsteps, so it gets just the labels, not the full step dicts.
    timed = _step_plan(record.get("frozen_duration"), [s["label"] for s in steps])  # may be None

    children = []
    for i, step in enumerate(steps):
        if status_list[i] == "resolved":
            status = "done"
        elif i == current_index:
            status = "current"
        else:
            status = "open"
        label = f"{timed[i]['start_label']}–{timed[i]['end_label']}: {step['label']}" if timed else step["label"]
        children.append({
            "id": f"{record['goal_id']}-step-{i}",
            "label": label,
            "status": status,
            # One level deep only - see module docstring. A microstep
            # is always "open": there is no per-microstep completion
            # signal today, only the per-step one (step_status above).
            "children": [
                {
                    "id": f"{record['goal_id']}-step-{i}-micro-{j}",
                    "label": microstep,
                    "status": "open",
                    "children": [],
                }
                for j, microstep in enumerate(step["microsteps"])
            ],
        })

    return {
        "id": f"goal-{record['goal_id']}",
        "label": record.get("goal", ""),
        "status": "done" if record.get("completed") else "current",
        "children": children,
    }
