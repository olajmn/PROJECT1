// The shapes of the data the server sends back, so TypeScript can catch
// mistakes. Only descriptions, no code that does anything. Matches what
// backend/api/answers_to_browser.py sends (project_view(), map_tree()).

// Contents
//  1. Map
//  2. Projects and chat
//  3. Simulated users
//  4. Paste
//  5. Model boundary (Settings → General)
//  6. Activity log (Settings → Logs)

// 1. Map

export interface MapNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  children: MapNode[];
}

// 2. Projects and chat
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
export interface TalkChartEntry {
  label: string;
  start: number;
  end: number;
  open: boolean;
  children: TalkChartEntry[];
  focus_step_id?: string;
}

export interface ProjectView {
  project_id: number;
  goal: string;
  completed: boolean;
  cancelled: boolean;
  sim_user_id: number | null;
  /** Latest history record timestamp for this project. */
  created_at?: string | null;
  node: MapNode | null;
  thread: ChatMessage[];
  talk: TalkChartEntry[];
}


// 3. Simulated users

export interface UserView {
  id: number;
  text: string;
  archived: boolean;
  created_at: string;
}

// 4. Paste

export interface PastedNode {
  label: string;
  children: PastedNode[];
}

export interface PastePreview {
  stripped: PastedNode[];
  kept: PastedNode[];
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
