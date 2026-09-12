// Frontend contract for agent/'s first web prototype (docs/v4-migration-decision.md).
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

/** One goal, as returned by GET /api/goals, POST /api/goals, and
 * POST /api/goals/<id>/feedback - matches server.py's _goal_view().
 * No natural-language `reply` here (unlike AgentResponse) - these
 * routes skip Node 1 entirely, see server.py's own docstring for why. */
export interface GoalView {
  goal_id: number;
  goal: string;
  completed: boolean;
  cancelled: boolean;
  vision_id: number | null;
  surface: string | null;
  node: PlanningNode | null;
}

/** One raw saved record, as returned by GET /api/history - matches
 * server.py's _history_view(). Every record ever saved, not just the
 * latest per goal (unlike GoalView) - a log entry, not a live status,
 * so no `node` tree here; `plan` is only the non-empty PLAN_KEYS/
 * clarification/suggested_* fields, in a fixed order. */
export interface HistoryEntry {
  id: number;
  goal_id: number;
  goal: string;
  duration: string | null;
  completed: boolean;
  cancelled: boolean;
  feedback: string | null;
  created_at: string;
  plan: Record<string, string>;
  step_count: number;
}

/** One Vision, as returned by GET /api/visions, POST /api/visions,
 * and POST /api/visions/<id>/archive - matches server.py's
 * _vision_view(). vision.ts itself only creates, lists, and archives
 * these; linking one to a Goal happens from active.ts's own card
 * (GoalView.vision_id, POST /api/goals/<id>/vision) instead. */
export interface VisionView {
  id: number;
  text: string;
  archived: boolean;
  created_at: string;
}

/** Which goal, if any, the free-conversation path is currently
 * "focused" on, as returned by GET/POST /api/chat-focus - matches
 * server.py's _chat_focus_view(). Mirrors cli.py's Session.
 * current_goal_id: null until the chat has touched a goal this
 * process, otherwise that goal's id and text.
 *
 * Named "chat focus", not "session" - cli.py's Session object happens
 * to hold this AND the persisted Session record below (SessionLogView)
 * as two attributes on one object, but they're different concepts;
 * see _chat_focus_view()'s own docstring for why this stays separate. */
export interface ChatFocusView {
  goal_id: number | null;
  goal: string | null;
}

/** One goal/plan event in a Session's derived log, as returned inside
 * GET /api/sessions - matches server.py's _session_goal_event().
 * `feedback` is null for the event that created the goal, otherwise
 * the feedback text that produced this particular replan. */
export interface SessionGoalEvent {
  goal_id: number;
  goal: string;
  feedback: string | null;
  created_at: string;
}

/** One Vision-creation event in a Session's derived log - matches
 * server.py's _session_vision_event(). Archiving isn't represented
 * here yet (see data_persistence.archive_vision()'s own docstring) -
 * only ever a creation event. */
export interface SessionVisionEvent {
  vision_id: number;
  text: string;
  created_at: string;
}

/** One persisted Session record plus everything that happened during
 * it, as returned by GET /api/sessions - matches server.py's
 * _session_log_view(). `ended_at` is a best-available boundary, not
 * necessarily a moment a real shutdown was ever observed: no
 * graceful-shutdown hook exists yet (see docs/04-current-state.md § 5),
 * so server.py's own route instead uses the next Session's
 * `started_at` as a stand-in end for every Session except the single
 * most recent one, which has no successor and is genuinely still
 * open (null). */
export interface SessionLogView {
  id: number;
  started_at: string;
  ended_at: string | null;
  goal_events: SessionGoalEvent[];
  vision_events: SessionVisionEvent[];
}
