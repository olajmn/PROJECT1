// Project workspace — Notion-ish shell over Project records.
// Left (sidebar): id#N menu + create + project list.
// Center: open project map. Close lives in the map's own top bar.
// Right: conversation for that project. Wire: project_id / /api/projects.

// Contents
//  1. Shell + state
//  2. Install panes
//  3. Data (load / replace / applyUsers)
//  4. Initialization

import { fetchProjects, fetchUsers } from "./api.js";
import { installChatResize, installSidebarResize } from "./shell/columnWidths.js";
import { installIdMenu } from "./panes/create/manager/manager.js";
import { renderManagerButton } from "./panes/create/manager/managerButton.js";
import { installProjectList } from "./panes/create/projectList.js";
import {
  detachArchivedOwners,
  ensureSelectionInActiveUser,
  projectsForActiveUser,
  syncActiveUser,
  type SelectionState,
} from "./panes/create/projectsForId.js";
import { installCreatePanel } from "./panes/create/createForm.js";
import { installChatPane } from "./panes/chat/chatPane.js";
import { installCommandMenu } from "./panes/chat/commands/menu.js";
import { installSendMessage } from "./panes/chat/sendMessage.js";
import { installMapPane } from "./panes/canvas/mapPane.js";
import { getActiveUserId, setActiveUserId } from "./user/activeId.js";
import { applyStoredTheme } from "./user/theme.js";
import type { ProjectView, UserView } from "./dataShapes.js";

applyStoredTheme();

// 1. Shell + state

const projectListEl = document.getElementById("project-list") as HTMLDivElement;
const listEmpty = document.getElementById("list-empty") as HTMLParagraphElement;
const projectListToggle = document.getElementById(
  "project-list-toggle",
) as HTMLButtonElement;
const sidebarBrand = document.getElementById("sidebar-brand") as HTMLButtonElement;
const sidebarIdHost = document.getElementById("sidebar-id") as HTMLElement;
const idMenuResize = document.getElementById("id-menu-resize") as HTMLElement;
const projectMain = document.getElementById("project-main") as HTMLElement;
const mainEmpty = document.getElementById("main-empty") as HTMLParagraphElement;
const projectChat = document.getElementById("project-chat") as HTMLElement;
const statusToggle = document.getElementById("status-toggle") as HTMLButtonElement;
const statusEl = document.getElementById("status-panel") as HTMLElement;
const statusResize = document.getElementById("status-resize") as HTMLElement;
const chatThread = document.getElementById("chat-thread") as HTMLDivElement;
const chatForm = document.getElementById("chat-form") as HTMLFormElement;
const chatInput = document.getElementById("chat-input") as HTMLTextAreaElement;
const chatCommandMenuHost = document.getElementById(
  "chat-command-menu-host",
) as HTMLElement;
const chatError = document.getElementById("chat-error") as HTMLParagraphElement;
const appShell = document.querySelector(".app-shell") as HTMLElement;
const workspace = document.querySelector(".workspace") as HTMLElement;
const sidebarResize = document.getElementById("sidebar-resize") as HTMLElement;
const chatResize = document.getElementById("chat-resize") as HTMLElement;

let projects: ProjectView[] = [];
let users: UserView[] = [];
const selection: SelectionState = {
  selectedId: null,
  selectedNodeId: null,
  selectedNodeLabel: null,
};

function selected(): ProjectView | null {
  return projects.find((p) => p.project_id === selection.selectedId) ?? null;
}

function ensureSel(): void {
  ensureSelectionInActiveUser(projects, selection);
}

function renderAll(): void {
  list.render();
  mapPane.render();
}

// 2. Install panes

const chatPane = installChatPane({
  statusPanel: statusEl,
  statusResize,
  statusToggle,
  threadEl: chatThread,
  onIsolateChange: () => mapPane.render(),
});

installSendMessage({
  form: chatForm,
  input: chatInput,
  errorEl: chatError,
  getProject: () => selected(),
  getSelectedNodeId: () => selection.selectedNodeId,
  getSelectedNodeLabel: () => selection.selectedNodeLabel,
  onUpdated: (updated) => replaceProject(updated),
});

installCommandMenu({
  host: chatCommandMenuHost,
  input: chatInput,
});

installSidebarResize(appShell, sidebarResize);
const chatRailApi = installChatResize(workspace, chatResize, projectChat);
for (const id of ["chat-rail-toggle", "chat-rail-grip"]) {
  document.getElementById(id)?.addEventListener("click", () => {
    chatRailApi.expand();
  });
}

const idMenu = installIdMenu({
  anchor: sidebarBrand,
  host: sidebarIdHost,
  resizeHandle: idMenuResize,
  getUsers: () => users,
  getProjects: () => projects,
  onUsersChanged: (next) => {
    applyUsers(next);
  },
  onProjectsUpdated: (updated) => {
    for (const u of updated) {
      projects = projects.map((p) =>
        p.project_id === u.project_id ? u : p,
      );
    }
    ensureSel();
    renderAll();
  },
  onActiveUserChanged: () => {
    ensureSel();
    if (selected()) createPanel.close();
    chatPane.clearIsolate();
    renderAll();
  },
  onSelectProject: (projectId) => {
    const target = projects.find((p) => p.project_id === projectId);
    if (!target) return;
    if (target.sim_user_id != null) {
      setActiveUserId(target.sim_user_id);
    }
    selection.selectedId = projectId;
    selection.selectedNodeId = null;
    selection.selectedNodeLabel = null;
    createPanel.close();
    chatPane.clearIsolate();
    renderAll();
  },
});

const createPanel = installCreatePanel({
  onNeedUser: () => idMenu.open(),
  onChange: () => mapPane.render(),
  getTitles: () => projectsForActiveUser(projects).map((p) => p.name),
  onCreated: (created) => {
    projects = [
      created,
      ...projects.filter((p) => p.project_id !== created.project_id),
    ];
    selection.selectedId = created.project_id;
    renderAll();
  },
});

const list = installProjectList({
  listEl: projectListEl,
  emptyEl: listEmpty,
  toggleEl: projectListToggle,
  getProjects: () => projects,
  getSelectedId: () => selection.selectedId,
  onSelectProject: (projectId) => {
    selection.selectedId = projectId;
    selection.selectedNodeId = null;
    selection.selectedNodeLabel = null;
    createPanel.close();
    chatPane.clearIsolate();
    renderAll();
  },
});

const mapPane = installMapPane({
  projectMain,
  mainEmpty,
  projectChat,
  chatInput,
  chatError,
  chatPane,
  getProject: () => selected(),
  isCreateOpen: () => createPanel.isOpen(),
  mountCreate: () => createPanel.mount(projectMain),
  getSelectedNodeId: () => selection.selectedNodeId,
  getSelectedNodeLabel: () => selection.selectedNodeLabel,
  setSelectedNode: (stepId, label) => {
    selection.selectedNodeId = stepId;
    selection.selectedNodeLabel = label;
  },
  onCloseProject: () => {
    selection.selectedId = null;
    selection.selectedNodeId = null;
    selection.selectedNodeLabel = null;
    chatPane.clearIsolate();
    renderAll();
  },
  onUpdated: (updated) => replaceProject(updated),
  onArchived: (projectId) => {
    projects = projects.filter((p) => p.project_id !== projectId);
    ensureSel();
    renderAll();
  },
  onBrandRender: () => renderManagerButton(sidebarBrand, idMenu.isOpen()),
});

// 3. Data

function applyUsers(next: UserView[]): void {
  users = next;
  projects = detachArchivedOwners(projects, next);
  syncActiveUser(next);
  ensureSel();
  renderAll();
  idMenu.refresh();
}

function replaceProject(updated: ProjectView): void {
  projects = projects.map((p) =>
    p.project_id === updated.project_id ? updated : p,
  );
  if (updated.completed || updated.cancelled) {
    projects = projects.filter((p) => p.project_id !== updated.project_id);
    ensureSel();
  } else {
    selection.selectedId = updated.project_id;
  }
  renderAll();
}

async function load(): Promise<void> {
  const [goals, allUsers] = await Promise.all([
    fetchProjects(),
    fetchUsers(),
  ]);
  projects = goals;
  users = allUsers;

  syncActiveUser(users);
  const params = new URLSearchParams(window.location.search);
  const want = Number(params.get("id"));
  if (want && projects.some((p) => p.project_id === want)) {
    const wanted = projects.find((p) => p.project_id === want)!;
    if (wanted.sim_user_id != null) {
      setActiveUserId(wanted.sim_user_id);
    }
    selection.selectedId = want;
  } else {
    ensureSel();
  }
  renderAll();
  idMenu.restoreIfRemembered();
  if (
    getActiveUserId() === null
    || params.get("tab") === "users"
    || params.get("tab") === "vision"
  ) {
    idMenu.open();
  }
}

// 4. Initialization

load().catch((err) => {
  listEmpty.hidden = false;
  listEmpty.textContent = `(error: ${(err as Error).message})`;
});
