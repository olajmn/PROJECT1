// Frontend contract for app/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.

// Contents
//  1. Plan tree (Projects map nodes)
//  2. Goals / Projects
//  3. Simulated users
//  4. Outline import
//  5. Model boundary (Settings → General)
//  6. Sessions (Settings → Logs)

// 1. Plan tree (Projects map nodes)

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
  /** Latest history record timestamp for this project. */
  created_at?: string | null;
  /** Open planner clarification, if any. */
  clarification?: string | null;
  surface: string | null;
  node: PlanningNode | null;
  thread: ChatMessage[];
  reply: string | null;
}

/** Same record as GoalView — product name for the Projects surface. */
export type ProjectView = GoalView;

// 3. Simulated users

export interface UserView {
  id: number;
  text: string;
  archived: boolean;
  created_at: string;
}

// 4. Outline import

export interface OutlineNode {
  label: string;
  children: OutlineNode[];
}

export interface OutlinePreview {
  stripped: OutlineNode[];
  kept: OutlineNode[];
}

// 5. Model boundary (Settings → General)

/** Read-only peek at llm_client's dials (GET /api/model). */
export interface ModelView {
  provider: string;
  model: string;
  temperature: number;
}

// 6. Sessions (Settings → Logs)

/** One HTTP process-run record from data/sessions.json. */
export interface SessionView {
  id: number;
  user_id: number;
  started_at: string;
  ended_at: string | null;
}
