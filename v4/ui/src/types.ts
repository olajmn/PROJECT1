// Frontend contract for v4's first web prototype (docs/architecture-v4.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.

/** A generic, capability-agnostic node - not a final domain model.
 * Present only when a Planning result actually had a step list to
 * show; most results won't, and that's expected (see PlanningResult). */
export interface PlanningNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  children: PlanningNode[];
}

/** The full response for one conversation turn, as returned by
 * POST /api/message - matches cli.py's process_turn() return shape. */
export interface AgentResponse {
  reply: string;
  capability: string | null;
  surface: string | null;
  node: PlanningNode | null;
  goal_id: number | null;
}
