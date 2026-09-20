// Project workspace — Notion-ish shell over Project records.
// Left (sidebar): id#N menu + create + project list.
// Center: open project map (topbar tabs).
// Right: conversation for that project. Wire: project_id / /api/projects.

// Contents
//  1. Shell
//  2. Selection helpers
//      - clearNodeSelection()
//      - isProgressionTree()
//      - selected()
//      - projectsForActiveUser()
//      - ensureSelectionInActiveUser()
//      - fillChatPlaceholder()
//  3. Rendering
//      - renderSidebarBrand()
//      - renderList()
//      - renderWorkspace()
//      - renderProjectTopbar()
//  4. Data
//      - applyUsers()
//      - replaceProject()
//      - load()
//  5. Event listeners
//  6. Initialization

import {
  addProgressionStep,
  cancelGoal,
  createGoal,
  fetchActiveGoals,
  fetchUsers,
  importProgressionOutline,
  removeProgressionStep,
  sendGoalFeedback,
  zoomGoalStep,
} from "../api.js";
import { installCollapseRail } from "../shell/columnRail/collapseRail.js";
import { installSidebarResize } from "../shell/columnResize.js";
import { setButtonBusy } from "../shell/busy.js";
import { renderTabStrip } from "../shell/tabs/tabStrip.js";
import type { TabStripItem } from "../shell/tabs/tabStrip.js";
import { installIdMenu } from "../sidebar/idMenu.js";
import {
  projectListIdLabel,
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "../sidebar/projectListOrder.js";
import { createIsolateChat } from "../chat/isolateChat.js";
import { treeWordsElement } from "../map/treeWords.js";
import type { NodeMenuActionId } from "../map/treeWords.js";
import { copyAsText } from "../map/copyAsText.js";
import { buildPasteTreePanel } from "../map/pasteTree.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
} from "../user/activeUser.js";
import type { ProjectView, UserView } from "../types.js";

const createForm = document.getElementById("create-form") as HTMLFormElement;
const createInput = document.getElementById("create-input") as HTMLTextAreaElement;
const createError = document.getElementById("create-error") as HTMLParagraphElement;
const projectList = document.getElementById("project-list") as HTMLDivElement;
const listEmpty = document.getElementById("list-empty") as HTMLParagraphElement;
const sidebarBrand = document.getElementById("sidebar-brand") as HTMLButtonElement;
const sidebarIdHost = document.getElementById("sidebar-id") as HTMLElement;
const projectTopbar = document.getElementById("project-topbar") as HTMLElement;
const projectMain = document.getElementById("project-main") as HTMLElement;
const mainEmpty = document.getElementById("main-empty") as HTMLParagraphElement;
const projectChat = document.getElementById("project-chat") as HTMLElement;
const chatThread = document.getElementById("chat-thread") as HTMLDivElement;
const chatForm = document.getElementById("chat-form") as HTMLFormElement;
const chatInput = document.getElementById("chat-input") as HTMLTextAreaElement;
const chatError = document.getElementById("chat-error") as HTMLParagraphElement;
const appShell = document.querySelector(".app-shell") as HTMLElement;
const workspace = document.querySelector(".workspace") as HTMLElement;
const sidebarResize = document.getElementById("sidebar-resize") as HTMLElement;
const chatResize = document.getElementById("chat-resize") as HTMLElement;

const PROGRESSION_STEP_ID = /^p\d+$/;
const DEFAULT_CHAT_PLACEHOLDER = "Talk about this project…";

let projects: ProjectView[] = [];
let users: UserView[] = [];
let selectedId: number | null = null;
/** Which map node is selected (click / Talk about this). */
let selectedNodeId: string | null = null;
let selectedNodeLabel: string | null = null;
let topTabProjectId: number | null = null;
/** Apply after switching back to Map from a chat focus click. */
let pendingMapFocus: { stepId: string; label: string } | null = null;

// 1. Shell

installSidebarResize(appShell, sidebarResize);
const chatRailApi = installCollapseRail({
  container: workspace,
  handle: chatResize,
  panel: projectChat,
  cssVar: "--chat-width",
  widthStorageKey: "projects.chatWidthPx",
  collapsedStorageKey: "projects.chatCollapsed",
  defaultWidth: 360,
  minWidth: 240,
  maxWidthCap: 720,
  minOther: 280,
  railWidth: 64,
  snapThreshold: 200,
  warnStart: 280,
  pendingClass: "is-collapse-pending",
  containerCollapsedClass: "is-chat-collapsed",
  panelCollapsedClass: "is-collapsed",
  bodyClass: "is-resizing-chat",
  widthFromPointer: (clientX, rect) => rect.right - clientX,
});
const chatRailToggle = document.getElementById(
  "chat-rail-toggle",
) as HTMLButtonElement;
chatRailToggle.addEventListener("click", () => {
  chatRailApi.expand();
});

const idMenu = installIdMenu({
  anchor: sidebarBrand,
  host: sidebarIdHost,
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
    ensureSelectionInActiveUser();
    renderList();
    renderWorkspace();
  },
  onActiveUserChanged: () => {
    ensureSelectionInActiveUser();
    isolateChat.clear();
    renderList();
    renderWorkspace();
    renderSidebarBrand();
  },
  onSelectProject: (projectId) => {
    const target = projects.find((p) => p.project_id === projectId);
    if (target?.sim_user_id != null) {
      setActiveUserId(target.sim_user_id);
    }
    selectedId = projectId;
    selectedNodeId = null;
    selectedNodeLabel = null;
    topTabProjectId = projectId;
    isolateChat.clear();
    renderList();
    renderWorkspace();
    renderSidebarBrand();
  },
});


const isolateChat = createIsolateChat({
  threadEl: chatThread,
  resolveStepId: (label) => {
    const rows = projectMain.querySelectorAll(".progress-row[data-step-id]");
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const text =
        row.querySelector(".progress-bead-btn, .progress-bead-label")
          ?.textContent ?? "";
      if (text === label) {
        return row.getAttribute("data-step-id");
      }
    }
    return null;
  },
  onChange: () => renderWorkspace(),
});

// 2. Selection helpers

/** Drop map focus — next chat is project-wide again. */
function clearNodeSelection(scope: ParentNode = projectMain): void {
  selectedNodeId = null;
  selectedNodeLabel = null;
  chatInput.placeholder = DEFAULT_CHAT_PLACEHOLDER;
  scope.querySelectorAll(".progress-row.is-selected").forEach((el) => {
    el.classList.remove("is-selected");
  });
  scope.querySelectorAll(".node-focus-note").forEach((el) => el.remove());
}

function isProgressionTree(node: { children: { id: string }[] }): boolean {
  return node.children.some((child) => PROGRESSION_STEP_ID.test(child.id));
}

function selected(): ProjectView | null {
  return projects.find((p) => p.project_id === selectedId) ?? null;
}

/** Projects owned by the active simulated user (sim_user_id). */
function projectsForActiveUser(): ProjectView[] {
  return projectsChronologicalForUser(projects, getActiveUserId());
}

function ensureSelectionInActiveUser(): void {
  const visible = projectsForActiveUser();
  if (selectedId !== null && visible.some((p) => p.project_id === selectedId)) {
    return;
  }
  // Newest under this id when nothing is selected yet.
  selectedId = visible.length > 0 ? visible[visible.length - 1].project_id : null;
  selectedNodeId = null;
  selectedNodeLabel = null;
}

function fillChatPlaceholder(text: string): void {
  chatThread.innerHTML = "";
  const note = document.createElement("p");
  note.className = "chat-placeholder";
  note.textContent = text;
  chatThread.appendChild(note);
}

// 3. Rendering

function renderList(): void {
  const visible = projectsForActiveUser();
  projectList.innerHTML = "";
  const userId = getActiveUserId();
  if (userId === null) {
    listEmpty.hidden = false;
    listEmpty.textContent = "Pick or create an id (click the label above) first.";
  } else {
    listEmpty.hidden = visible.length > 0;
    listEmpty.textContent =
      visible.length > 0 ? "" : "No projects for this id yet.";
  }
  for (const project of projectsNewestFirst(visible)) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "project-list-item";
    if (project.project_id === selectedId) {
      button.classList.add("is-selected");
    }
    const title = document.createElement("span");
    title.className = "project-list-title";
    title.textContent = project.goal;
    const id = document.createElement("span");
    id.className = "entity-id";
    id.textContent = projectListIdLabel(visible, project);
    button.append(title, id);
    button.addEventListener("click", () => {
      selectedId = project.project_id;
      selectedNodeId = null;
      selectedNodeLabel = null;
      topTabProjectId = project.project_id;
      isolateChat.clear();
      renderList();
      renderWorkspace();
    });
    projectList.appendChild(button);
  }
}

function renderWorkspace(): void {
  const project = selected();
  projectMain.innerHTML = "";
  projectTopbar.innerHTML = "";
  chatError.hidden = true;

  renderSidebarBrand();
  renderProjectTopbar(project);

  if (!project) {
    projectMain.appendChild(mainEmpty);
    mainEmpty.hidden = false;
    mainEmpty.textContent =
      getActiveUserId() === null
        ? "Pick or create an id (sidebar label above Create), then add a project."
        : "No project selected — create one in the sidebar.";
    projectChat.hidden = false;
    fillChatPlaceholder("Select a project to open its chat.");
    return;
  }

  mainEmpty.hidden = true;
  projectChat.hidden = false;

  if (topTabProjectId !== project.project_id) {
    topTabProjectId = project.project_id;
  }

  const body = document.createElement("div");
  body.className = "project-body";

  // Map is the hero — do not park the planner's Action/`now` surface
  // (e.g. "print Hello World") above the tree. Chat still carries
  // agent lines via the thread.

  // Progress outline: project root / middle steps (ASCII tree).
  // + nests; click selects; ⋯ = Add here / Suggest / Talk about this.
  const middle = project.node?.children ?? [];
  const canSelect = project.node ? isProgressionTree(project.node) : false;
  let line: HTMLDivElement;

  const markSelected = (stepId: string, note: string) => {
    selectedNodeId = stepId;
    const row = line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
    const label =
      row?.querySelector(".progress-bead-btn, .progress-bead-label")
        ?.textContent ?? stepId;
    selectedNodeLabel = label;
    chatInput.placeholder = `About “${label}”…`;
    line.querySelectorAll(".progress-row.is-selected").forEach((el) => {
      el.classList.remove("is-selected");
    });
    row?.classList.add("is-selected");
    let focus = body.querySelector(".node-focus-note") as HTMLParagraphElement | null;
    if (!focus) {
      focus = document.createElement("p");
      focus.className = "node-focus-note";
      line.insertAdjacentElement("afterend", focus);
    }
    focus.textContent = note;
  };

  const nodeLabel = (stepId: string): string => {
    const row = line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
    return (
      row?.querySelector(".progress-bead-btn, .progress-bead-label")
        ?.textContent ?? stepId
    );
  };

  const addBead = async (trimmed: string, parentId?: string) => {
    line.classList.add("plan-busy");
    try {
      const updated = await addProgressionStep(
        project.project_id,
        trimmed,
        parentId,
      );
      replaceProject(updated);
    } catch (err) {
      line.classList.remove("plan-busy");
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      line.appendChild(error);
    }
  };
  const removeBead = async (stepId: string) => {
    line.classList.add("plan-busy");
    try {
      const updated = await removeProgressionStep(project.project_id, stepId);
      // Removing the currently-selected node would otherwise leave
      // selectedNodeId pointing at a step that no longer exists -
      // silently stale until the next action (Paste structure, Talk
      // about this, a chat send) targets a node that's already gone.
      if (stepId === selectedNodeId) {
        selectedNodeId = null;
        selectedNodeLabel = null;
        chatInput.placeholder = DEFAULT_CHAT_PLACEHOLDER;
      }
      replaceProject(updated);
    } catch (err) {
      line.classList.remove("plan-busy");
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      line.appendChild(error);
    }
  };

  const paste = buildPasteTreePanel({
    getParentLabel: () => selectedNodeLabel,
    getParentId: () => selectedNodeId,
    getGoalId: () => project.project_id,
    onImported: (updated) => replaceProject(updated),
  });

  const onMenuAction = async (action: NodeMenuActionId, stepId: string) => {
    const label = nodeLabel(stepId);
    if (action === "register") {
      markSelected(stepId, `Add under: ${label}`);
      const row = line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
      const addBtn = row?.querySelector(
        ".progress-add-inline",
      ) as HTMLButtonElement | null;
      addBtn?.click();
      return;
    }
    if (action === "analyze") {
      markSelected(stepId, `Talk about: ${label}`);
      chatInput.focus();
      return;
    }
    if (action === "paste") {
      markSelected(stepId, `Will import under: ${label}`);
      paste.open();
      return;
    }
    // suggest — agent proposes children (old zoom, on request only)
    markSelected(stepId, `Suggesting under: ${label}…`);
    line.classList.add("plan-busy");
    try {
      const childCount = (id: string): number => {
        const walk = (
          n: { id: string; children: typeof n[] } | null | undefined,
        ): number | null => {
          if (!n) return null;
          if (n.id === id) return n.children.length;
          for (const c of n.children) {
            const hit = walk(c);
            if (hit !== null) return hit;
          }
          return null;
        };
        return walk(project.node) ?? 0;
      };
      const beforeCount = childCount(stepId);
      const updated = await zoomGoalStep(project.project_id, stepId);
      const afterWalk = (
        n: { id: string; children: typeof n[] } | null | undefined,
      ): number | null => {
        if (!n) return null;
        if (n.id === stepId) return n.children.length;
        for (const c of n.children) {
          const hit = afterWalk(c);
          if (hit !== null) return hit;
        }
        return null;
      };
      const afterCount = afterWalk(updated.node) ?? 0;
      replaceProject(updated);
      if (afterCount <= beforeCount) {
        const note = document.createElement("p");
        note.className = "node-focus-note";
        note.textContent =
          "Nothing more to suggest under that node — already fine enough.";
        projectMain
          .querySelector(".progress-line")
          ?.insertAdjacentElement("afterend", note);
      }
    } catch (err) {
      line.classList.remove("plan-busy");
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      line.appendChild(error);
    }
  };

  line = treeWordsElement(
    project.goal,
    middle,
    canSelect
      ? (stepId: string) => {
          markSelected(stepId, `Looking at: ${nodeLabel(stepId)}`);
          if (paste.isOpen()) paste.updatePasteHint();
        }
      : undefined,
    addBead,
    removeBead,
    null,
    selectedNodeId,
    canSelect ? onMenuAction : undefined,
    `#${project.project_id}`,
  );
  body.appendChild(line);

  const copyRow = document.createElement("div");
  copyRow.className = "map-copy-row";
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "map-copy-button";
  copyBtn.textContent = "Copy as ASCII";
  copyBtn.title = "Copy a classic text tree for docs or chat";
  copyBtn.addEventListener("click", async () => {
    const text = copyAsText(
      project.goal,
      middle,
      `#${project.project_id}`,
    );
    try {
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = "Copied";
      window.setTimeout(() => {
        copyBtn.textContent = "Copy as ASCII";
      }, 1200);
    } catch {
      copyBtn.textContent = "Copy failed";
      window.setTimeout(() => {
        copyBtn.textContent = "Copy as ASCII";
      }, 1500);
    }
  });
  copyRow.append(copyBtn, paste.pasteBtn);
  body.appendChild(copyRow);
  body.appendChild(paste.pasteForm);

  // Click empty map space (not a node row) to unselect focus.
  body.addEventListener("click", (event) => {
    // The open paste form's target node IS the current selection - an
    // incidental click on empty canvas must not swap the import target.
    if (paste.isOpen()) return;
    const target = event.target as Element | null;
    if (!target) return;
    if (target.closest(".progress-row")) return;
    if (target.closest(".progress-add-form")) return;
    if (target.closest(".map-copy-row")) return;
    if (target.closest(".map-paste-form")) return;
    clearNodeSelection(body);
  });

  if (!project.node) {
    const hint = document.createElement("p");
    hint.className = "project-hint";
    hint.textContent =
      "Add steps with +, or talk — a plan from the agent is optional.";
    body.appendChild(hint);
  }

  projectMain.appendChild(body);

  if (pendingMapFocus) {
    const focus = pendingMapFocus;
    pendingMapFocus = null;
    markSelected(focus.stepId, `Looking at: ${focus.label}`);
  }

  isolateChat.fill(project.thread ?? [], (stepId, label) => {
    markSelected(stepId, `Looking at: ${label}`);
    if (paste.isOpen()) paste.updatePasteHint();
  });
}

function renderSidebarBrand(): void {
  const active = getActiveUserId();
  sidebarBrand.textContent = active !== null ? userLabel(active) : "id";
  if (!idMenu.isOpen()) {
    sidebarBrand.classList.remove("is-active");
  }
  sidebarBrand.setAttribute(
    "aria-label",
    active !== null
      ? "Active id. Click to switch or create ids."
      : "No active id. Click to create or pick one.",
  );
}

function renderProjectTopbar(project: ProjectView | null): void {
  if (!project) {
    projectTopbar.hidden = true;
    return;
  }

  projectTopbar.hidden = false;

  const items: TabStripItem[] = [
    {
      id: "map",
      label: project.goal,
      selected: true,
      onSelect: () => {
        renderWorkspace();
      },
      onClose: () => {
        selectedId = null;
        selectedNodeId = null;
        selectedNodeLabel = null;
        topTabProjectId = null;
        isolateChat.clear();
        renderList();
        renderWorkspace();
      },
    },
  ];

  projectTopbar.appendChild(renderTabStrip(items));

  const actions = document.createElement("div");
  actions.className = "card-actions";
  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "cancel-button";
  cancelButton.textContent = `Archive “${project.goal}”`;
  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await cancelGoal(project.project_id);
      projects = projects.filter((p) => p.project_id !== project.project_id);
      ensureSelectionInActiveUser();
      topTabProjectId = selectedId;
      renderList();
      renderWorkspace();
    } catch (err) {
      cancelButton.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      projectTopbar.appendChild(error);
    }
  });
  actions.appendChild(cancelButton);
  projectTopbar.appendChild(actions);
}

// 4. Data

function applyUsers(next: UserView[]): void {
  users = next;
  const activeIds = new Set(
    next.filter((v) => !v.archived).map((v) => v.id),
  );
  projects = projects.map((p) =>
    p.sim_user_id != null && !activeIds.has(p.sim_user_id)
      ? { ...p, sim_user_id: null }
      : p,
  );
  renderList();
  renderWorkspace();
  idMenu.refresh();
}

function replaceProject(updated: ProjectView): void {
  projects = projects.map((p) =>
    p.project_id === updated.project_id ? updated : p,
  );
  if (updated.completed || updated.cancelled) {
    projects = projects.filter((p) => p.project_id !== updated.project_id);
    ensureSelectionInActiveUser();
  } else {
    selectedId = updated.project_id;
  }
  renderList();
  renderWorkspace();
}

async function load(): Promise<void> {
  const [goals, allUsers] = await Promise.all([
    fetchActiveGoals(),
    fetchUsers(),
  ]);
  projects = goals;
  users = allUsers;

  const activeUsers = users.filter((v) => !v.archived);
  let active = getActiveUserId();
  if (active !== null && !activeUsers.some((u) => u.id === active)) {
    setActiveUserId(null);
    active = null;
  }
  if (active === null && activeUsers.length === 1) {
    setActiveUserId(activeUsers[0].id);
  }
  const params = new URLSearchParams(window.location.search);
  const want = Number(params.get("id"));
  if (want && projects.some((p) => p.project_id === want)) {
    const wanted = projects.find((p) => p.project_id === want)!;
    if (wanted.sim_user_id != null) {
      setActiveUserId(wanted.sim_user_id);
    }
    selectedId = want;
  } else {
    ensureSelectionInActiveUser();
  }
  renderList();
  renderWorkspace();
  if (
    getActiveUserId() === null
    || params.get("tab") === "users"
    || params.get("tab") === "vision"
  ) {
    idMenu.open();
  }
}

// 5. Event listeners

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = createInput.value.trim();
  if (!text) return;
  const userId = getActiveUserId();
  if (userId === null) {
    createError.hidden = false;
    createError.textContent =
      "(pick or create an id — click the label above Create)";
    idMenu.open();
    return;
  }
  const createButton = createForm.querySelector(
    'button[type="submit"]',
  ) as HTMLButtonElement;
  createInput.disabled = true;
  setButtonBusy(createButton, true);
  createError.hidden = true;
  try {
    const created = await createGoal(text, userId);
    createInput.value = "";
    projects = [
      created,
      ...projects.filter((p) => p.project_id !== created.project_id),
    ];
    selectedId = created.project_id;
    topTabProjectId = created.project_id;
    renderList();
    renderWorkspace();
  } catch (err) {
    createError.hidden = false;
    createError.textContent = `(error: ${(err as Error).message})`;
  } finally {
    createInput.disabled = false;
    setButtonBusy(createButton, false);
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const project = selected();
  if (!project) return;
  const text = chatInput.value.trim();
  if (!text) return;
  const sendButton = chatForm.querySelector(
    'button[type="submit"]',
  ) as HTMLButtonElement;
  chatInput.disabled = true;
  setButtonBusy(sendButton, true);
  chatError.hidden = true;
  try {
    // A multi-line paste while focused on a node is imported as
    // children of that node instead of sent as an ordinary chat
    // message - only on Send, not on paste itself (a paste is just
    // text arriving in the compose box, same as typing it; it should
    // not act on its own before the user chooses to send it). Falls
    // back to an ordinary message if nothing recognizable parses out.
    // unwrap=false (keep everything) - unlike the Paste structure
    // form, chat has no preview to catch a wrong guess before it
    // happens, so the safe default is an extra node the user can
    // remove afterward (visible, reversible), never a silently
    // discarded one they never see.
    let updated;
    if (selectedNodeId && text.includes("\n")) {
      try {
        updated = await importProgressionOutline(
          project.project_id,
          text,
          selectedNodeId,
          false,
        );
      } catch {
        updated = await sendGoalFeedback(
          project.project_id,
          text,
          selectedNodeLabel,
          selectedNodeId,
        );
      }
    } else {
      updated = await sendGoalFeedback(
        project.project_id,
        text,
        selectedNodeLabel,
        selectedNodeId,
      );
    }
    chatInput.value = "";
    replaceProject(updated);
  } catch (err) {
    chatError.hidden = false;
    chatError.textContent = `(error: ${(err as Error).message})`;
  } finally {
    chatInput.disabled = false;
    setButtonBusy(sendButton, false);
  }
});

// 6. Initialization

load().catch((err) => {
  listEmpty.hidden = false;
  listEmpty.textContent = `(error: ${(err as Error).message})`;
});
