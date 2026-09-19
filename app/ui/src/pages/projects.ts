// Project workspace prototype — Notion-ish shell over the existing
// goal_id backend. Left: project list + create. Center: open project
// (intent + structure). Right/bottom: conversation for that project.
// No new persistence model; ProjectView is the project record
// (alias of GoalView — same /api/goals wire shape).

import {
  addProgressionStep,
  cancelGoal,
  createGoal,
  fetchActiveGoals,
  fetchVisions,
  importProgressionOutline,
  removeProgressionStep,
  sendGoalFeedback,
  setGoalVision,
  zoomGoalStep,
} from "../api.js";
import { installChatResize, installSidebarResize } from "../shell/columnResize.js";
import { createIsolateChat } from "../chat/isolateChat.js";
import { treeWordsElement } from "../map/treeWords.js";
import type { NodeMenuActionId } from "../map/treeWords.js";
import { copyAsText } from "../map/copyAsText.js";
import { buildPasteTreePanel } from "../map/pasteTree.js";
import type { ProjectView, VisionView } from "../types.js";

const createForm = document.getElementById("create-form") as HTMLFormElement;
const createInput = document.getElementById("create-input") as HTMLTextAreaElement;
const createError = document.getElementById("create-error") as HTMLParagraphElement;
const projectList = document.getElementById("project-list") as HTMLDivElement;
const listEmpty = document.getElementById("list-empty") as HTMLParagraphElement;
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

installSidebarResize(appShell, sidebarResize);
installChatResize(workspace, chatResize);

const PROGRESSION_STEP_ID = /^p\d+$/;
const DEFAULT_CHAT_PLACEHOLDER = "Talk about this project…";

let projects: ProjectView[] = [];
let visions: VisionView[] = [];
let selectedId: number | null = null;
/** Which map node is selected (click / Talk about this). */
let selectedNodeId: string | null = null;
let selectedNodeLabel: string | null = null;

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
  return projects.find((p) => p.goal_id === selectedId) ?? null;
}

function renderList(): void {
  projectList.innerHTML = "";
  listEmpty.hidden = projects.length > 0;
  for (const project of projects) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "project-list-item";
    if (project.goal_id === selectedId) {
      button.classList.add("is-selected");
    }
    const title = document.createElement("span");
    title.className = "project-list-title";
    title.textContent = project.goal;
    const id = document.createElement("span");
    id.className = "entity-id";
    id.textContent = `#${project.goal_id}`;
    button.append(title, id);
    button.addEventListener("click", () => {
      selectedId = project.goal_id;
      selectedNodeId = null;
      selectedNodeLabel = null;
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

  if (!project) {
    projectMain.appendChild(mainEmpty);
    mainEmpty.hidden = false;
    projectTopbar.hidden = true;
    projectChat.hidden = true;
    return;
  }

  mainEmpty.hidden = true;
  projectTopbar.hidden = false;
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
        project.goal_id,
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
      const updated = await removeProgressionStep(project.goal_id, stepId);
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
    getGoalId: () => project.goal_id,
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
      const updated = await zoomGoalStep(project.goal_id, stepId);
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
    `#${project.goal_id}`,
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
      `#${project.goal_id}`,
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

  // Vision link + Archive live in the topbar, outside the map canvas
  // (project-main) — not competing with the map, and not bottom-of-
  // canvas either, since the canvas scrolls and this shouldn't.
  const visionForm = document.createElement("form");
  visionForm.className = "vision-link-form";
  const select = document.createElement("select");
  const noneOption = document.createElement("option");
  noneOption.value = "";
  noneOption.textContent = "Vision: none";
  select.appendChild(noneOption);
  for (const vision of visions) {
    const option = document.createElement("option");
    option.value = String(vision.id);
    option.textContent = `Vision: ${vision.text}`;
    if (project.vision_id === vision.id) option.selected = true;
    select.appendChild(option);
  }
  const visionButton = document.createElement("button");
  visionButton.type = "submit";
  visionButton.textContent = "Update vision";
  visionForm.append(select, visionButton);
  visionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const raw = select.value;
    try {
      const updated = await setGoalVision(
        project.goal_id,
        raw ? Number(raw) : null,
      );
      replaceProject(updated);
    } catch (err) {
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      visionForm.appendChild(error);
    }
  });
  projectTopbar.appendChild(visionForm);

  const actions = document.createElement("div");
  actions.className = "card-actions";
  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "cancel-button";
  cancelButton.textContent = "Archive project";
  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await cancelGoal(project.goal_id);
      projects = projects.filter((p) => p.goal_id !== project.goal_id);
      selectedId = projects[0]?.goal_id ?? null;
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

  isolateChat.fill(project.thread ?? [], (stepId, label) => {
    markSelected(stepId, `Looking at: ${label}`);
    if (paste.isOpen()) paste.updatePasteHint();
  });
}

function replaceProject(updated: ProjectView): void {
  projects = projects.map((p) =>
    p.goal_id === updated.goal_id ? updated : p,
  );
  if (updated.completed || updated.cancelled) {
    projects = projects.filter((p) => p.goal_id !== updated.goal_id);
    selectedId = projects[0]?.goal_id ?? null;
  } else {
    selectedId = updated.goal_id;
  }
  renderList();
  renderWorkspace();
}

async function load(): Promise<void> {
  const [goals, allVisions] = await Promise.all([
    fetchActiveGoals(),
    fetchVisions(),
  ]);
  projects = goals;
  visions = allVisions.filter((v) => !v.archived);
  const params = new URLSearchParams(window.location.search);
  const want = Number(params.get("id"));
  if (want && projects.some((p) => p.goal_id === want)) {
    selectedId = want;
  } else if (projects.length > 0 && selectedId === null) {
    selectedId = projects[0].goal_id;
  }
  renderList();
  renderWorkspace();
}

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = createInput.value.trim();
  if (!text) return;
  createInput.disabled = true;
  createError.hidden = true;
  try {
    const created = await createGoal(text);
    createInput.value = "";
    projects = [created, ...projects.filter((p) => p.goal_id !== created.goal_id)];
    selectedId = created.goal_id;
    renderList();
    renderWorkspace();
  } catch (err) {
    createError.hidden = false;
    createError.textContent = `(error: ${(err as Error).message})`;
  } finally {
    createInput.disabled = false;
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const project = selected();
  if (!project) return;
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.disabled = true;
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
          project.goal_id,
          text,
          selectedNodeId,
          false,
        );
      } catch {
        updated = await sendGoalFeedback(
          project.goal_id,
          text,
          selectedNodeLabel,
          selectedNodeId,
        );
      }
    } else {
      updated = await sendGoalFeedback(
        project.goal_id,
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
  }
});

load().catch((err) => {
  listEmpty.hidden = false;
  listEmpty.textContent = `(error: ${(err as Error).message})`;
});
