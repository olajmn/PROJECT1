// Frontend contract for agent/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.

// Contents
//  1. Plan tree
//      - PlanningNode
//  2. Free conversation
//      - AgentResponse
//  3. Goals
//      - ChatMessage
//      - GoalView
//      - HistoryEntry
//  4. Vision
//      - VisionView
//  5. Chat focus
//      - ChatFocusView
//  6. Session log
//      - SessionGoalEvent
//      - SessionVisionEvent
//      - SessionLogView

// 1. Plan tree

/** A generic, capability-agnostic node - not a final domain model.
 * Present only when a Planning result actually had a step list to
 * show; most results won't, and that's expected (see PlanningResult). */
/** One node of the Steps page's scratch tree (POST /api/tree,
 * server.py's _step_view()). Deliberately NOT PlanningNode: it has a
 * stable per-step `id` and a `zoomed` flag, neither of which exists
 * in a plan record's two-level shape, and it recurses to any depth.
 * See backend/planning/plan/step.py. */
export interface StepNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  /** False means "never zoomed into", not "nothing under it" - a
   * zoomed step with no children is one an Action can be projected
   * from directly (see backend/planning/plan/zoom.py). */
  zoomed: boolean;
  children: StepNode[];
}

export interface TreeView {
  /** The time phrase extracted from the typed text - a step can't be
   * decomposed without the span it has to fit inside. */
  duration: string;
  root: StepNode | null;
}

export interface PlanningNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  children: PlanningNode[];
}

// 2. Free conversation

/** The full response for one conversation turn, as returned by
 * POST /api/message - matches cli.py's process_turn() return shape. */
export interface AgentResponse {
  reply: string;
  capability: string | null;
  surface: string | null;
  node: PlanningNode | null;
  goal_id: number | null;
}

// 3. Goals

/** One goal, as returned by GET /api/goals, POST /api/goals, and
 * POST /api/goals/<id>/feedback - matches server.py's _goal_view().
 * `reply` is set only after a chat turn (POST feedback); GET leaves
 * it null and the thread uses surface_text for every agent line. */
export interface ChatMessage {
  role: "user" | "agent";
  text: string;
  /** Map node this turn was about (Talk about this / Looking at). */
  focus?: string;
  /** Progression step id for that node, when known. */
  focus_step_id?: string;
}

export interface GoalView {
  goal_id: number;
  goal: string;
  completed: boolean;
  cancelled: boolean;
  vision_id: number | null;
  surface: string | null;
  node: PlanningNode | null;
  thread: ChatMessage[];
  reply: string | null;
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

// 4. Vision

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

// 5. Chat focus

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

// 6. Session log

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
