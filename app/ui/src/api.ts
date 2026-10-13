// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

// Contents
//  1. Projects
//      - fetchProjects(), createProject(), renameProject()
//      - archiveProject(), setProjectUser()
//      - fetchArchivedProjects(), restoreProject(), deleteProject()
//  2. Map
//      - addNode(), removeNode(), moveNode()
//      - pasteText(), previewPaste(), pasteNodes()
//      - chooseFolder(), addFolder()
//  3. Chat
//      - sendChatMessage()
//  4. Accounts
//      - fetchAccounts(), createAccount(), renameAccount()
//      - archiveAccount(), restoreAccount(), deleteAccount()
//  5. Model (Settings → General)
//      - fetchModel()
//  6. Activity log (Settings → Logs)
//      - fetchLog(), fetchProjectTimeline()
//  7. Saved trees
//      - saveTree(), fetchSavedTrees(), insertSavedTree(), deleteSavedTree()
//  8. Demo session
//      - fetchSession(), logIn(), logOut()

import type { ProjectView, LogEntry, ModelView, PastedNode, PastePreview, AccountView, SavedTreeView, SessionView } from "./dataShapes.js";

/** Every request in this file goes through here. In demo mode a 401
 *  means the session has ended (docs/public-demo-plan.md), so the page
 *  goes to the login screen instead of showing an error. */
function fetch(input: string, init?: RequestInit): Promise<Response> {
  return globalThis.fetch(input, init).then((res) => {
    if (res.status === 401 && !input.startsWith("/api/login")) {
      window.location.assign("/login.html");
    }
    return res;
  });
}

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
  accountId?: number | null,
): Promise<ProjectView> {
  const body: { text: string; account_id?: number } = {
    text,
  };
  if (accountId != null) {
    body.account_id = accountId;
  }
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    // The server puts its plain reason in the status line (send_error).
    throw new Error(res.statusText || `request failed: ${res.status}`);
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

export async function fetchArchivedProjects(): Promise<ProjectView[]> {
  const res = await fetch("/api/projects/archived");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView[];
}

export async function restoreProject(projectId: number): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/restore`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function deleteProject(projectId: number): Promise<void> {
  const res = await fetch(`/api/projects/${projectId}/delete`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

export async function setProjectUser(projectId: number, accountId: number | null): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ account_id: accountId }),
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

/** One place up or down among its siblings; id and children go with it. */
export async function moveNode(
  projectId: number,
  stepId: string,
  direction: "up" | "down",
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/map/${stepId}/move-${direction}`, {
    method: "POST",
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

// 3. Chat

export async function sendChatMessage(
  projectId: number,
  text: string,
  focusLabel?: string | null,
  focusStepId?: string | null,
  focusDay?: string | null,
): Promise<ProjectView> {
  const body: {
    text: string;
    focus_label?: string;
    focus_step_id?: string;
    focus_day?: string;
  } = { text };
  if (focusLabel) {
    body.focus_label = focusLabel;
  }
  if (focusStepId) {
    body.focus_step_id = focusStepId;
  }
  if (focusDay) {
    body.focus_day = focusDay;
  }
  const res = await fetch(`/api/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    // The server puts its plain reason in the status line (send_error).
    throw new Error(res.statusText || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

// 4. Accounts

export async function fetchAccounts(): Promise<AccountView[]> {
  const res = await fetch("/api/accounts");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as AccountView[];
}


export async function createAccount(text: string): Promise<AccountView> {
  const res = await fetch("/api/accounts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}


export async function renameAccount(
  accountId: number,
  text: string,
): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}


export async function archiveAccount(accountId: number): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/archive`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as AccountView;
}


export async function restoreAccount(accountId: number): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/restore`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}

export async function deleteAccount(accountId: number): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/delete`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
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

/** One page of the activity log, newest first; `offset` = entries
 *  already shown (backend/api/activity_log.py LOG_LIMIT per page). */
export async function fetchLog(offset = 0): Promise<LogEntry[]> {
  const res = await fetch(offset > 0 ? `/api/log?offset=${offset}` : "/api/log");
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

// 7. Saved trees

/** Store this node and everything under it as structure (no ids). */
export async function saveTree(
  projectId: number,
  stepId: string,
): Promise<SavedTreeView> {
  const res = await fetch(
    `/api/projects/${projectId}/map/${encodeURIComponent(stepId)}/save-tree`,
    { method: "POST" },
  );
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as SavedTreeView;
}

/** The saved trees of this project's account, newest first. */
export async function fetchSavedTrees(
  projectId: number,
): Promise<SavedTreeView[]> {
  const res = await fetch(`/api/projects/${projectId}/saved-trees`);
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as SavedTreeView[];
}

/** Insert a saved tree as new nodes (fresh ids) under `parentId`, or
 *  at the top level when it is null. */
export async function insertSavedTree(
  projectId: number,
  treeId: string,
  parentId: string | null,
): Promise<ProjectView> {
  const body: { tree_id: string; parent_id?: string } = { tree_id: treeId };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/insert-tree`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function deleteSavedTree(treeId: string): Promise<void> {
  const res = await fetch(
    `/api/saved-trees/${encodeURIComponent(treeId)}/delete`,
    { method: "POST" },
  );
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

// 8. Demo session

/** Whether the server runs in demo mode (login, sandboxes). */
export async function fetchSession(): Promise<SessionView> {
  const res = await fetch("/api/session");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionView;
}

export async function logIn(password: string): Promise<void> {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

export async function logOut(): Promise<void> {
  await fetch("/api/logout", { method: "POST" });
}
