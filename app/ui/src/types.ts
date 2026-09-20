// Frontend contract for app/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.

// Contents
//  1. Plan tree
//  2. Goals / Projects
//  3. Simulated users
//  4. Session log
//  5. Outline import / Steps tree (see below)

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

// 2. Goals / Projects
//
// Wire identity is project_id / /api/projects. Display text field
// remains `goal` until a later rename.

export interface ChatMessage {
  role: "user" | "agent";
  text: string;
  focus?: string;
  focus_step_id?: string;
}

export interface GoalView {
  project_id: number;
  goal: string;
  completed: boolean;
  cancelled: boolean;
  sim_user_id: number | null;
  /** Open planner clarification, if any. */
  clarification?: string | null;
  surface: string | null;
  node: PlanningNode | null;
  thread: ChatMessage[];
  reply: string | null;
}

/** Same record as GoalView — product name for the Projects surface. */
export type ProjectView = GoalView;

export function projectIdOf(view: { project_id?: number | null }): number {
  if (view.project_id == null) {
    throw new Error("missing project_id");
  }
  return view.project_id;
}

export interface HistoryEntry {
  id: number;
  project_id: number;
  goal: string;
  duration: string | null;
  completed: boolean;
  cancelled: boolean;
  feedback: string | null;
  created_at: string;
  plan: Record<string, string>;
  step_count: number;
}

// 3. Simulated users

export interface UserView {
  id: number;
  text: string;
  archived: boolean;
  created_at: string;
}

// 4. Session log

export interface SessionGoalEvent {
  project_id: number;
  goal: string;
  feedback: string | null;
  created_at: string;
}

export interface SessionUserEvent {
  sim_user_id: number;
  text: string;
  created_at: string;
}

export interface SessionLogView {
  id: number;
  started_at: string;
  ended_at: string | null;
  goal_events: SessionGoalEvent[];
  user_events: SessionUserEvent[];
}

// 5. Outline import

export interface OutlineNode {
  label: string;
  children: OutlineNode[];
}

export interface OutlinePreview {
  stripped: OutlineNode[];
  kept: OutlineNode[];
}
