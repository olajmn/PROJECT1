// Project workspace — Notion-ish shell over Project records.
// Left (sidebar): id#N menu + create + project list.
// Center: open project map. Close lives in the map's own top bar.
// Right: conversation for that project. Wire: project_id / /api/projects.

// Contents
//  1. Shell
//      - element handles + module state
//      - chatRailApi / idMenu / createPanel / isolateChat / chatChart
//  2. Selection helpers
//      - clearNodeSelection()
//      - isProgressionTree()
//      - selected()
//      - projectsForActiveUser()
//      - ensureSelectionInActiveUser()
//      - fillChatPlaceholder()
//  3. Rendering
//      - renderList()
//      - renderWorkspace()
//      - renderSidebarBrand()
//  4. Data
//      - applyUsers()
//      - replaceProject()
//      - load()
//  5. Event listeners
//  6. Initialization

import {
  addProgressionStep,
  cancelGoal,
  fetchActiveGoals,
  fetchUsers,
  importProgressionOutline,
  readTree,
  removeProgressionStep,
  sendGoalFeedback,
  zoomGoalStep,
} from "../api.js";
import { installChatResize, installSidebarResize } from "../shell/columnResize.js";
import { setButtonBusy } from "../shell/busy.js";
import { installIdMenu } from "../sidebar/idMenu/index.js";
import {
  projectListIdLabel,
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "../sidebar/projectListOrder.js";
import { createIsolateChat } from "../chat/isolateChat.js";
import { messageRow } from "../chat/messageRow.js";
import { printMapText } from "../chat/printMap.js";
import { createChatChart } from "../chat/chart/index.js";
import { installCreatePanel } from "../create/panel.js";
import { displayProjectTitle } from "../create/autoname.js";
import { treeWordsElement } from "../map/treeWords.js";
import type { NodeMenuActionId } from "../map/treeWords.js";
import { installMapScale } from "../map/frame/index.js";
import { copyAsText } from "../map/copyAsText.js";
import { buildAddFolderPanel } from "../map/addFolder.js";
import { buildPasteTreePanel } from "../map/pasteTree.js";
import {
  getActiveUserId,
  setActiveUserId,
  getLastProjectId,
  setLastProjectId,
  ID_BRAND,
} from "../user/activeUser.js";
import { applyStoredTheme } from "../user/theme.js";
import type { ProjectView, UserView } from "../types.js";

applyStoredTheme();

const projectList = document.getElementById("project-list") as HTMLDivElement;
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
const chatChartToggle = document.getElementById(
  "chat-chart-toggle",
) as HTMLButtonElement;
const chatChartEl = document.getElementById("chat-chart") as HTMLElement;
const chatChartResize = document.getElementById("chat-chart-resize") as HTMLElement;
const chatThread = document.getElementById("chat-thread") as HTMLDivElement;
const chatForm = document.getElementById("chat-form") as HTMLFormElement;
const chatInput = document.getElementById("chat-input") as HTMLTextAreaElement;
const chatPrintMap = document.getElementById("chat-print-map") as HTMLButtonElement;
const chatError = document.getElementById("chat-error") as HTMLParagraphElement;
const appShell = document.querySelector(".app-shell") as HTMLElement;
const workspace = document.querySelector(".workspace") as HTMLElement;
const sidebarResize = document.getElementById("sidebar-resize") as HTMLElement;
const chatResize = document.getElementById("chat-resize") as HTMLElement;

const PROGRESSION_STEP_ID = /^p\d+$/;
const DEFAULT_CHAT_PLACEHOLDER = "Talk about this project…";
/** Manual show/hide for #project-list, independent of Manager's own
 * open state (renderList() hides it whichever is off — see § 3). */
const PROJECT_LIST_OPEN_KEY = "projects.listOpen";

function readListManuallyOpen(): boolean {
  try {
    const stored = localStorage.getItem(PROJECT_LIST_OPEN_KEY);
    return stored === null ? true : stored === "1";
  } catch {
    return true;
  }
}

let projects: ProjectView[] = [];
let users: UserView[] = [];
let selectedId: number | null = null;
/** Which map node is selected (click / Talk about this). */
let selectedNodeId: string | null = null;
let selectedNodeLabel: string | null = null;
/** Apply after switching back to Map from a chat focus click. */
let pendingMapFocus: { stepId: string; label: string } | null = null;
let listManuallyOpen = readListManuallyOpen();

// 1. Shell

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

const chatChart = createChatChart(
  chatChartEl,
  chatChartResize,
  chatChartToggle,
);

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
    ensureSelectionInActiveUser();
    renderList();
    renderWorkspace();
  },
  onActiveUserChanged: () => {
    ensureSelectionInActiveUser();
    // Switching id should reveal that id's project — don't keep Create over it.
    if (selected()) createPanel.close();
    chatChart.clearSelection();
    isolateChat.clear();
    renderList();
    renderWorkspace();
    renderSidebarBrand();
  },
  onSelectProject: (projectId) => {
    const target = projects.find((p) => p.project_id === projectId);
    if (!target) return;
    if (target.sim_user_id != null) {
      setActiveUserId(target.sim_user_id);
    }
    selectedId = projectId;
    selectedNodeId = null;
    selectedNodeLabel = null;
    createPanel.close();
    chatChart.clearSelection();
    isolateChat.clear();
    renderList();
    renderWorkspace();
    renderSidebarBrand();
  },
});

const createPanel = installCreatePanel({
  onNeedUser: () => idMenu.open(),
  onChange: () => renderWorkspace(),
  getTitles: () => projectsForActiveUser().map((p) => p.goal),
  onCreated: (created) => {
    projects = [
      created,
      ...projects.filter((p) => p.project_id !== created.project_id),
    ];
    selectedId = created.project_id;
    renderList();
    renderWorkspace();
  },
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
  updatePrintButton();
}

function updatePrintButton(): void {
  const hasProject = selected() != null && !createPanel.isOpen();
  chatPrintMap.disabled = !hasProject;
  if (selectedNodeId) {
    chatPrintMap.textContent = "Print path";
    chatPrintMap.title = "Print this node's path as stored on the map";
  } else {
    chatPrintMap.textContent = "Print map";
    chatPrintMap.title = "Print the stored map labels";
  }
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
  // Nothing selected yet — resume the last project seen under this id,
  // falling back to newest if that one's gone (deleted, wrong user, ...).
  const activeUserId = getActiveUserId();
  const lastId = activeUserId !== null ? getLastProjectId(activeUserId) : null;
  const resumed = visible.find((p) => p.project_id === lastId);
  selectedId = resumed
    ? resumed.project_id
    : visible.length > 0
      ? visible[visible.length - 1].project_id
      : null;
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
  // Visibility is manual only, via project-list-toggle — independent of
  // whether Manager (idMenu) is open.
  const listVisible = listManuallyOpen;
  projectListToggle.classList.toggle("is-active", listVisible);
  projectListToggle.setAttribute("aria-expanded", String(listVisible));
  if (!listVisible) {
    projectList.hidden = true;
    projectList.innerHTML = "";
    listEmpty.hidden = true;
    return;
  }
  projectList.hidden = false;
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
    title.textContent = displayProjectTitle(project.goal);
    const id = document.createElement("span");
    id.className = "entity-id";
    id.textContent = projectListIdLabel(visible, project);
    button.append(title, id);
    button.addEventListener("click", () => {
      selectedId = project.project_id;
      selectedNodeId = null;
      selectedNodeLabel = null;
      createPanel.close();
      chatChart.clearSelection();
      isolateChat.clear();
      renderList();
      renderWorkspace();
    });
    projectList.appendChild(button);
  }
}

function renderWorkspace(): void {
  const project = selected();
  // Only ever record a real project. Writing null here would erase where
  // you were every time the middle pane shows something else.
  const activeUserId = getActiveUserId();
  if (activeUserId !== null && project) {
    setLastProjectId(activeUserId, project.project_id);
  }
  projectMain.innerHTML = "";
  chatError.hidden = true;

  renderSidebarBrand();

  // No project, or Create pressed over one: the middle pane is where a
  // project is made. Clicking the project in the sidebar is the way back.
  if (!project || createPanel.isOpen()) {
    projectMain.appendChild(mainEmpty);
    mainEmpty.hidden = false;
    mainEmpty.textContent =
      getActiveUserId() === null
        ? "Pick or create an id above, then name a project."
        : "Name a new project.";
    createPanel.mount(projectMain);
    projectChat.hidden = false;
    fillChatPlaceholder("Select a project to open its chat.");
    updatePrintButton();
    return;
  }

  mainEmpty.hidden = true;
  projectChat.hidden = false;

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
      const scaleHost =
        (line.closest(".map-scale-viewport") as HTMLElement | null) ?? line;
      scaleHost.insertAdjacentElement("afterend", focus);
    }
    focus.textContent = note;
    updatePrintButton();
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
  const folder = buildAddFolderPanel({
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
      const form = row?.querySelector(
        ".progress-add-form",
      ) as HTMLFormElement | null;
      if (form) {
        form.hidden = false;
        const input = form.querySelector(
          ".progress-add-input",
        ) as HTMLInputElement | null;
        input?.focus();
      }
      return;
    }
    if (action === "remove") {
      await removeBead(stepId);
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
          .querySelector(".map-scale-viewport, .progress-line")
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
    displayProjectTitle(project.goal),
    middle,
    canSelect
      ? (stepId: string) => {
          markSelected(stepId, `Looking at: ${nodeLabel(stepId)}`);
          if (paste.isOpen()) paste.updatePasteHint();
          if (folder.isOpen()) folder.updateFolderHint();
        }
      : undefined,
    addBead,
    removeBead,
    selectedNodeId,
    canSelect ? onMenuAction : undefined,
    `#${project.project_id}`,
  );
  body.appendChild(line);
  installMapScale(body, line, project.project_id, {
    onClose: () => {
      selectedId = null;
      selectedNodeId = null;
      selectedNodeLabel = null;
      chatChart.clearSelection();
      isolateChat.clear();
      renderList();
      renderWorkspace();
    },
  });

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
  const readBtn = document.createElement("button");
  readBtn.type = "button";
  readBtn.className = "map-copy-button";
  readBtn.textContent = "Read map";
  readBtn.title = "Ask what this map looks to be about";
  readBtn.addEventListener("click", async () => {
    setButtonBusy(readBtn, true);
    try {
      const reading = await readTree(project.project_id);
      // Shown, never saved — gone on the next render, by design.
      chatThread.append(
        messageRow({ role: "agent", text: reading.summary }),
      );
      chatThread.scrollTop = chatThread.scrollHeight;
    } catch (err) {
      chatError.hidden = false;
      chatError.textContent = `(error: ${(err as Error).message})`;
    } finally {
      setButtonBusy(readBtn, false);
    }
  });

  const copyGroup = document.createElement("div");
  copyGroup.className = "map-copy-group";
  copyGroup.append(copyBtn, paste.pasteBtn, folder.folderBtn, readBtn);

  const archiveBtn = document.createElement("button");
  archiveBtn.type = "button";
  archiveBtn.className = "map-copy-button";
  archiveBtn.textContent = `Archive “${displayProjectTitle(project.goal)}”`;
  archiveBtn.addEventListener("click", async () => {
    archiveBtn.disabled = true;
    try {
      await cancelGoal(project.project_id);
      projects = projects.filter((p) => p.project_id !== project.project_id);
      ensureSelectionInActiveUser();
      renderList();
      renderWorkspace();
    } catch (err) {
      archiveBtn.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      copyRow.appendChild(error);
    }
  });

  copyRow.append(copyGroup, archiveBtn);
  body.appendChild(copyRow);
  body.appendChild(paste.pasteForm);
  body.appendChild(folder.folderForm);

  // Click empty map space (not a node row) to unselect focus.
  body.addEventListener("click", (event) => {
    // The open paste form's target node IS the current selection - an
    // incidental click on empty canvas must not swap the import target.
    if (paste.isOpen() || folder.isOpen()) return;
    const target = event.target as Element | null;
    if (!target) return;
    if (target.closest(".progress-row")) return;
    if (target.closest(".progress-add-form")) return;
    if (target.closest(".map-copy-row")) return;
    if (target.closest(".map-paste-form")) return;
    if (target.closest(".map-folder-form")) return;
    clearNodeSelection(body);
  });

  if (!project.node) {
    const hint = document.createElement("p");
    hint.className = "project-hint";
    hint.textContent =
      "Add steps with +, or talk — a plan from the agent is optional.";
    // Above the bottom bar, not below it: the bar is a status line flush
    // with the column's bottom edge (css/map/pane.css), and the sidebar's
    // own footer rule lines up with it. A paragraph underneath pushed the
    // bar off that line whenever a project had no tree yet. The hint also
    // belongs with the empty canvas it describes, not under the actions.
    body.insertBefore(hint, copyRow);
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
    if (folder.isOpen()) folder.updateFolderHint();
  });
  chatChart.fill(project.talk, (sequence) => {
    isolateChat.isolateRange(sequence.start, sequence.end, sequence.label);
    if (sequence.focus_step_id) {
      markSelected(sequence.focus_step_id, `Looking at: ${sequence.label}`);
    }
    renderWorkspace();
  });
  updatePrintButton();
}

function renderSidebarBrand(): void {
  const active = getActiveUserId();
  sidebarBrand.textContent = ID_BRAND;
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
  // If active points at a deleted id (or was cleared), pick a live one so
  // Create/Seed and the Projects list don't say "pick an id" while one exists.
  syncActiveUser(next);
  ensureSelectionInActiveUser();
  renderList();
  renderWorkspace();
  idMenu.refresh();
}

/** Keep localStorage active id aligned with non-archived users. */
function syncActiveUser(nextUsers: UserView[]): void {
  const live = nextUsers.filter((u) => !u.archived);
  const active = getActiveUserId();
  if (active !== null && live.some((u) => u.id === active)) return;
  if (live.length === 0) {
    setActiveUserId(null);
    return;
  }
  setActiveUserId(live.reduce((a, b) => (a.id > b.id ? a : b)).id);
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

  syncActiveUser(users);
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
  idMenu.restoreIfRemembered();
  if (
    getActiveUserId() === null
    || params.get("tab") === "users"
    || params.get("tab") === "vision"
  ) {
    idMenu.open();
  }
}

// 5. Event listeners

chatPrintMap.addEventListener("click", () => {
  const project = selected();
  if (!project) return;
  const text = printMapText(project.node, selectedNodeId);
  chatThread.append(messageRow({ role: "agent", text }));
  chatThread.scrollTop = chatThread.scrollHeight;
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

projectListToggle.addEventListener("click", () => {
  listManuallyOpen = !listManuallyOpen;
  try {
    localStorage.setItem(PROJECT_LIST_OPEN_KEY, listManuallyOpen ? "1" : "0");
  } catch {
    /* private mode / quota — manual toggle is best-effort */
  }
  renderList();
});

// 6. Initialization

load().catch((err) => {
  listEmpty.hidden = false;
  listEmpty.textContent = `(error: ${(err as Error).message})`;
});
