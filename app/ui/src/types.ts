// Frontend contract for app/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what backend/api/answers_to_browser.py
// (project_view(), map_tree()) already reduced a project record to,
// and nothing more.

// Contents
//  1. Plan tree (Projects map nodes)
//  2. Goals / Projects
//  3. Simulated users
//  4. Outline import
//  5. Model boundary (Settings → General)
//  6. Activity log (Settings → Logs)

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

/** One About-stretch in the derived talk tree (not the file map). */
export interface TalkSequence {
  label: string;
  start: number;
  end: number;
  open: boolean;
  children: TalkSequence[];
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
  node: PlanningNode | null;
  thread: ChatMessage[];
  talk: TalkSequence[];
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

// 6. Activity log (Settings → Logs)

/** One saved change, from backend/api/activity_log.py activity_log(). */
export interface LogEntry {
  at: string | null;
  project_id: number | null;
  project: string;
  kind: "Created" | "Chat" | "Map" | "Owner" | "Cancelled";
  text: string;
}
