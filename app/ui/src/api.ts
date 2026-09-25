// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

// Contents
//  1. Projects
//      - fetchProjects(), createProject(), renameProject()
//      - archiveProject(), setProjectUser()
//  2. Map
//      - addNode(), removeNode(), suggestChildren()
//      - pasteText(), previewPaste(), pasteNodes()
//      - chooseFolder(), addFolder(), readMap()
//  3. Chat
//      - sendChatMessage()
//  4. Simulated users
//      - fetchUsers(), createUser(), archiveUser()
//  5. Model (Settings → General)
//      - fetchModel()
//  6. Activity log (Settings → Logs)
//      - fetchLog(), fetchProjectTimeline()

import type { ProjectView, LogEntry, ModelView, PastedNode, PastePreview, UserView } from "./dataShapes.js";

async function httpErrorMessage(res: Response): Promise<string> {
  const detail = (await res.text()).trim();
  const fromHtml =
    detail.match(/Error code: \d+[\s\S]*?<p>([^<]+)/i)?.[1]?.trim() ??
    detail.match(/<p>([^<]+)<\/p>/i)?.[1]?.trim();
  const plain = (fromHtml || detail || `request failed: ${res.status}`).replace(/\s+/g, " ");
  return plain.slice(0, 240);
}

// 1. Projects

export async function fetchProjects(): Promise<ProjectView[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView[];
}

/** Mint a project: `text` is the name, canvas starts empty. */
export async function createProject(
  text: string,
  simUserId?: number | null,
): Promise<ProjectView> {
  const body: { text: string; sim_user_id?: number } = {
    text,
  };
  if (simUserId != null) {
    body.sim_user_id = simUserId;
  }
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** Replace the project's display name. Identity stays project_id. */
export async function renameProject(
  projectId: number,
  text: string,
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/name`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function archiveProject(projectId: number): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/cancel`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function setProjectUser(projectId: number, simUserId: number | null): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sim_user_id: simUserId }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

// 2. Map

export async function addNode(
  projectId: number,
  label: string,
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { label: string; parent_id?: string } = { label };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function removeNode(projectId: number, stepId: string): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/map/${stepId}/remove`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function suggestChildren(projectId: number, stepId: string): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/suggest/${stepId}`, { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    // send_error() returns an HTML page; pull the plain reason if present.
    const plain = detail.match(/no timeframe[\s\S]*?(?=<|$)/i)?.[0]
      ?? detail.match(/Error code: (\d+)[\s\S]*?<p>([^<]+)/i)?.[2]
      ?? detail.match(/cannot zoom[^.<]*/i)?.[0];
    throw new Error((plain || detail || `request failed: ${res.status}`).slice(0, 200));
  }
  return (await res.json()) as ProjectView;
}

export async function pasteText(
  projectId: number,
  text: string,
  parentId?: string | null,
  unwrap = true,
): Promise<ProjectView> {
  const body: { text: string; parent_id?: string; unwrap: boolean } = {
    text,
    unwrap,
  };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** Dry-run parse_outline() both ways (title line dropped / kept) so
 * the paste form can show what would be created before committing -
 * no project needed, nothing saved. */
export async function previewPaste(text: string): Promise<PastePreview> {
  const res = await fetch("/api/parse-outline-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as PastePreview;
}

/** Import an already-built {"label", "children"} tree directly - no
 * text parsing, no unwrap guess - for when the caller already has the
 * exact shape the user chose (ui/'s preview, after toggling nodes
 * in/out). See import_map_outline()'s own `forest` param. */
export async function pasteNodes(
  projectId: number,
  nodes: PastedNode[],
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { nodes: PastedNode[]; parent_id?: string } = { nodes };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** macOS folder dialog. Empty string means the user cancelled. */
export async function chooseFolder(): Promise<string> {
  const res = await fetch("/api/choose-folder", { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  const body = (await res.json()) as { path?: string };
  return body.path ?? "";
}

export async function addFolder(
  projectId: number,
  folder: string,
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { path: string; parent_id?: string } = { path: folder };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/folder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export interface MapReading {
  summary: string;
}

/**
 * Read an existing map back into words — what the project looks to be
 * about. Nothing is saved; the reading is gone on the next render.
 */
export async function readMap(projectId: number): Promise<MapReading> {
  const res = await fetch(`/api/projects/${projectId}/read`, { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as MapReading;
}

// 3. Chat

export async function sendChatMessage(
  projectId: number,
  text: string,
  focusLabel?: string | null,
  focusStepId?: string | null,
): Promise<ProjectView> {
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
  const res = await fetch(`/api/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

// 4. Simulated users

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

// 5. Model (Settings → General)

export async function fetchModel(): Promise<ModelView> {
  const res = await fetch("/api/model");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ModelView;
}

// 6. Activity log (Settings → Logs)

export async function fetchLog(): Promise<LogEntry[]> {
  const res = await fetch("/api/log");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as LogEntry[];
}

/** One project's full history, oldest first (ungrouped). */
export async function fetchProjectTimeline(
  projectId: number,
): Promise<LogEntry[]> {
  const res = await fetch(`/api/projects/${projectId}/timeline`);
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as LogEntry[];
}
