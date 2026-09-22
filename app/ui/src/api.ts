// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

// Contents
//  1. Goals / Projects
//      - fetchActiveGoals()
//      - createGoal()
//      - sendGoalFeedback()
//      - cancelGoal()
//      - setProjectUser()
//  2. Simulated users
//      - fetchUsers()
//      - createUser()
//      - archiveUser()
//  3. Outline import helpers (used by Projects)
//  4. Model boundary (Settings → General)
//  5. Sessions (Settings → Logs)

import type { GoalView, ModelView, OutlineNode, OutlinePreview, SessionView, UserView } from "./types.js";

async function httpErrorMessage(res: Response): Promise<string> {
  const detail = (await res.text()).trim();
  const fromHtml =
    detail.match(/Error code: \d+[\s\S]*?<p>([^<]+)/i)?.[1]?.trim() ??
    detail.match(/<p>([^<]+)<\/p>/i)?.[1]?.trim();
  const plain = (fromHtml || detail || `request failed: ${res.status}`).replace(/\s+/g, " ");
  return plain.slice(0, 240);
}

// 1. Goals / Projects

export async function fetchActiveGoals(): Promise<GoalView[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView[];
}

/**
 * `planned: false` skips the planner — `text` becomes the project's
 * name and the tree is built or pasted afterwards.
 */
export async function createGoal(
  text: string,
  simUserId?: number | null,
  planned = true,
): Promise<GoalView> {
  const body: { text: string; sim_user_id?: number; planned?: boolean } = {
    text,
  };
  if (simUserId != null) {
    body.sim_user_id = simUserId;
  }
  if (!planned) {
    body.planned = false;
  }
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function sendGoalFeedback(
  goalId: number,
  text: string,
  focusLabel?: string | null,
  focusStepId?: string | null,
): Promise<GoalView> {
  const body: {
    text: string;
    focus_label?: string;
    focus_step_id?: string;
  } = { text };
  if (focusLabel) {
    body.focus_label = focusLabel;
  }
  if (focusStepId) {
    body.focus_step_id = focusStepId;
  }
  const res = await fetch(`/api/projects/${goalId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function cancelGoal(goalId: number): Promise<GoalView> {
  const res = await fetch(`/api/projects/${goalId}/cancel`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function setProjectUser(goalId: number, simUserId: number | null): Promise<GoalView> {
  const res = await fetch(`/api/projects/${goalId}/user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sim_user_id: simUserId }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as GoalView;
}

export async function zoomGoalStep(goalId: number, stepId: string): Promise<GoalView> {
  const res = await fetch(`/api/projects/${goalId}/zoom/${stepId}`, { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    // send_error() returns an HTML page; pull the plain reason if present.
    const plain = detail.match(/no timeframe[\s\S]*?(?=<|$)/i)?.[0]
      ?? detail.match(/Error code: (\d+)[\s\S]*?<p>([^<]+)/i)?.[2]
      ?? detail.match(/cannot zoom[^.<]*/i)?.[0];
    throw new Error((plain || detail || `request failed: ${res.status}`).slice(0, 200));
  }
  return (await res.json()) as GoalView;
}

export async function addProgressionStep(
  goalId: number,
  label: string,
  parentId?: string | null,
): Promise<GoalView> {
  const body: { label: string; parent_id?: string } = { label };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${goalId}/progression`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function importProgressionOutline(
  goalId: number,
  text: string,
  parentId?: string | null,
  unwrap = true,
): Promise<GoalView> {
  const body: { text: string; parent_id?: string; unwrap: boolean } = {
    text,
    unwrap,
  };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${goalId}/progression/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export interface TreeReading {
  summary: string;
}

/**
 * Read an existing map back into words — what the project looks to be
 * about. Nothing is saved; the reading is gone on the next render.
 */
export async function readTree(goalId: number): Promise<TreeReading> {
  const res = await fetch(`/api/projects/${goalId}/read`, { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as TreeReading;
}

/** Dry-run parse_outline() both ways (title line dropped / kept) so
 * the paste form can show what would be created before committing -
 * no goal needed, nothing saved. */
export async function previewOutline(text: string): Promise<OutlinePreview> {
  const res = await fetch("/api/parse-outline-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as OutlinePreview;
}

/** Import an already-built {"label", "children"} tree directly - no
 * text parsing, no unwrap guess - for when the caller already has the
 * exact shape the user chose (ui/'s preview, after toggling nodes
 * in/out). See import_progression_outline()'s own `forest` param. */
export async function importProgressionForest(
  goalId: number,
  nodes: OutlineNode[],
  parentId?: string | null,
): Promise<GoalView> {
  const body: { nodes: OutlineNode[]; parent_id?: string } = { nodes };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${goalId}/progression/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function removeProgressionStep(goalId: number, stepId: string): Promise<GoalView> {
  const res = await fetch(`/api/projects/${goalId}/progression/${stepId}/remove`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

// 2. Simulated users

export async function fetchUsers(): Promise<UserView[]> {
  const res = await fetch("/api/users");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as UserView[];
}

export async function createUser(text: string): Promise<UserView> {
  const res = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as UserView;
}

export async function archiveUser(simUserId: number): Promise<UserView> {
  const res = await fetch(`/api/users/${simUserId}/archive`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as UserView;
}

// 4. Model boundary (Settings → General)

export async function fetchModel(): Promise<ModelView> {
  const res = await fetch("/api/model");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ModelView;
}

// 5. Sessions (Settings → Logs)

export async function fetchSessions(): Promise<SessionView[]> {
  const res = await fetch("/api/sessions");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionView[];
}
