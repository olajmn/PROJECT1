// Frontend contract for app/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.

// Contents
//  1. Plan tree
//  2. Free conversation
//  3. Goals / Projects
//  4. Vision
//  5. Chat focus
//  6. Session log

// 1. Plan tree

export interface StepNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  zoomed: boolean;
  children: StepNode[];
}

export interface TreeView {
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

/** POST /api/message — process_turn() return shape. project_id is
 * canonical; goal_id is a deprecated mirror (Phase B). */
export interface AgentResponse {
  reply: string;
  capability: string | null;
  surface: string | null;
  node: PlanningNode | null;
  project_id: number | null;
  /** @deprecated use project_id */
  goal_id?: number | null;
}

// 3. Goals / Projects
//
// Wire identity is project_id / /api/projects (Phase B). Display text
// field remains `goal` until a later rename.

export interface ChatMessage {
  role: "user" | "agent";
  text: string;
  focus?: string;
  focus_step_id?: string;
}

export interface GoalView {
  project_id: number;
  /** @deprecated use project_id */
  goal_id?: number;
  goal: string;
  completed: boolean;
  cancelled: boolean;
  vision_id: number | null;
  surface: string | null;
  node: PlanningNode | null;
  thread: ChatMessage[];
  reply: string | null;
}

/** Same record as GoalView — product name for the Projects surface. */
export type ProjectView = GoalView;

/** Resolve identity from a view that may still carry the deprecated mirror. */
export function projectIdOf(view: {
  project_id?: number | null;
  goal_id?: number | null;
}): number {
  const id = view.project_id ?? view.goal_id;
  if (id == null) {
    throw new Error("missing project_id");
  }
  return id;
}

export interface HistoryEntry {
  id: number;
  project_id: number;
  /** @deprecated use project_id */
  goal_id?: number;
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

export interface VisionView {
  id: number;
  text: string;
  archived: boolean;
  created_at: string;
}

// 5. Chat focus

export interface ChatFocusView {
  project_id: number | null;
  /** @deprecated use project_id */
  goal_id?: number | null;
  goal: string | null;
}

// 6. Session log

export interface SessionGoalEvent {
  project_id: number;
  /** @deprecated use project_id */
  goal_id?: number;
  goal: string;
  feedback: string | null;
  created_at: string;
}

export interface SessionVisionEvent {
  vision_id: number;
  text: string;
  created_at: string;
}

export interface SessionLogView {
  id: number;
  started_at: string;
  ended_at: string | null;
  goal_events: SessionGoalEvent[];
  vision_events: SessionVisionEvent[];
}

// 7. Outline import

export interface OutlineNode {
  label: string;
  children: OutlineNode[];
}

export interface OutlinePreview {
  stripped: OutlineNode[];
  kept: OutlineNode[];
}
