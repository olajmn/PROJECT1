// Project workspace prototype — Notion-ish shell over the existing
// goal_id backend. Left: project list + create. Center: open project
// (intent + structure). Right/bottom: conversation for that project.
// No new persistence model; GoalView is the project record.

import {
  addProgressionStep,
  cancelGoal,
  createGoal,
  fetchActiveGoals,
  fetchVisions,
  importProgressionForest,
  importProgressionOutline,
  previewOutline,
  removeProgressionStep,
  sendGoalFeedback,
  setGoalVision,
  zoomGoalStep,
} from "./api.js";
import { installChatResize, installSidebarResize } from "./columnResize.js";
import { progressLineElement } from "./tree.js";
import { projectMapToAscii } from "./asciiMap.js";
import type { NodeMenuActionId } from "./tree.js";
import type { ChatMessage, GoalView, OutlineNode, VisionView } from "./types.js";

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

let projects: GoalView[] = [];
let visions: VisionView[] = [];
let selectedId: number | null = null;
/** Which map node is selected (click / Talk about this). */
let selectedNodeId: string | null = null;
let selectedNodeLabel: string | null = null;
/** Chat thread filtered to one "About X" focus label, or null for the full thread. */
let isolatedFocus: string | null = null;
/** Full-thread scroll position to restore after leaving isolation, instead of snapping to bottom. */
let preIsolationScrollTop: number | null = null;

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

function selected(): GoalView | null {
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
      isolatedFocus = null;
      renderList();
      renderWorkspace();
    });
    projectList.appendChild(button);
  }
}

function messageRow(message: ChatMessage): HTMLDivElement {
  const row = document.createElement("div");
  row.className = `message message-${message.role === "user" ? "you" : "agent"}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = message.role === "user" ? "You" : "Agent";
  const body = document.createElement("span");
  body.className = "text";
  body.textContent = message.text;
  row.append(label, body);
  return row;
}

/** Paste structure preview node: parse_outline()'s {"label",
 * "children"} plus a per-node, user-toggled `excluded` flag - every
 * node is clickable, not just a single outer title, so the user can
 * drop any label at any depth and keep its children (see
 * applyExclusions()). Plain and local to the preview; not the live
 * map's own layout/SVG, since this is a before-import sketch. */
interface PreviewNode {
  label: string;
  children: PreviewNode[];
  excluded: boolean;
}

function toPreviewNode(node: OutlineNode, excluded: boolean): PreviewNode {
  return {
    label: node.label,
    children: node.children.map((c) => toPreviewNode(c, false)),
    excluded,
  };
}

/** An excluded node drops out, but its children are promoted to
 * where it stood - the same "this label is just a wrapper, keep what
 * is under it" idea generalized from the single-root case to any
 * node at any depth. */
function applyExclusions(nodes: PreviewNode[]): OutlineNode[] {
  const result: OutlineNode[] = [];
  for (const node of nodes) {
    const children = applyExclusions(node.children);
    if (node.excluded) {
      result.push(...children);
    } else {
      result.push({ label: node.label, children });
    }
  }
  return result;
}

function previewTreeElement(
  nodes: PreviewNode[],
  onToggle: (node: PreviewNode) => void,
): HTMLUListElement {
  const list = document.createElement("ul");
  list.className = "outline-preview-list";
  for (const node of nodes) {
    const item = document.createElement("li");
    const label = document.createElement("span");
    label.className = "outline-preview-title-toggle";
    label.classList.toggle("is-excluded", node.excluded);
    label.textContent = node.label;
    label.title = node.excluded
      ? "Click to keep this as its own node"
      : "Click to drop this as its own node (its children still import)";
    label.addEventListener("click", () => onToggle(node));
    item.appendChild(label);
    if (node.children.length > 0) {
      item.appendChild(previewTreeElement(node.children, onToggle));
    }
    list.appendChild(item);
  }
  return list;
}

/** Resolve a tree step id from a focus label when history has no id. */
function stepIdForFocusLabel(label: string): string | null {
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
}

function isolationBanner(): HTMLDivElement {
  const banner = document.createElement("div");
  banner.className = "thread-isolation-banner";
  const label = document.createElement("span");
  label.textContent = `Showing only: About “${isolatedFocus}”`;
  const back = document.createElement("button");
  back.type = "button";
  back.className = "thread-isolation-back";
  back.textContent = "← Show full conversation";
  back.addEventListener("click", () => {
    isolatedFocus = null;
    renderWorkspace();
  });
  banner.append(label, back);
  return banner;
}

function fillThread(
  messages: ChatMessage[],
  onFocusClick?: (stepId: string, label: string) => void,
): void {
  chatThread.innerHTML = "";

  if (isolatedFocus) {
    chatThread.appendChild(isolationBanner());
    for (const message of messages) {
      if ((message.focus?.trim() || null) !== isolatedFocus) continue;
      chatThread.appendChild(messageRow(message));
    }
    chatThread.scrollTop = chatThread.scrollHeight;
    return;
  }

  let section: HTMLDivElement | null = null;
  let sectionFocus: string | null = null;

  for (const message of messages) {
    const focus = message.focus?.trim() || null;
    if (focus !== sectionFocus) {
      sectionFocus = focus;
      if (focus) {
        const frame = document.createElement("div");
        frame.className = "chat-focus-section";
        frame.dataset.focusLabel = focus;
        const stepId = message.focus_step_id?.trim();
        if (stepId) frame.dataset.focusStepId = stepId;
        if (onFocusClick) {
          frame.classList.add("is-clickable");
          frame.title = `Select “${focus}” on the map`;
          frame.addEventListener("click", () => {
            const label = frame.dataset.focusLabel || focus;
            const id =
              frame.dataset.focusStepId ||
              stepIdForFocusLabel(label) ||
              null;
            if (id) onFocusClick(id, label);
          });
        }
        const header = document.createElement("div");
        header.className = "chat-focus-header";
        const marker = document.createElement("span");
        marker.className = "chat-focus-marker";
        marker.textContent = `About “${focus}”`;
        const isolateBtn = document.createElement("button");
        isolateBtn.type = "button";
        isolateBtn.className = "thread-isolate-button";
        isolateBtn.textContent = "Show only this →";
        isolateBtn.addEventListener("click", (event) => {
          event.stopPropagation();
          preIsolationScrollTop = chatThread.scrollTop;
          isolatedFocus = focus;
          renderWorkspace();
        });
        header.append(marker, isolateBtn);
        frame.appendChild(header);
        chatThread.appendChild(frame);
        section = frame;
      } else {
        section = null;
      }
    } else if (
      focus &&
      section &&
      message.focus_step_id &&
      !section.dataset.focusStepId
    ) {
      section.dataset.focusStepId = message.focus_step_id.trim();
    }
    (section ?? chatThread).appendChild(messageRow(message));
  }
  if (preIsolationScrollTop !== null) {
    chatThread.scrollTop = preIsolationScrollTop;
    preIsolationScrollTop = null;
  } else {
    chatThread.scrollTop = chatThread.scrollHeight;
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
      pasteForm.hidden = false;
      updatePasteHint();
      pasteForm.scrollIntoView({ behavior: "smooth", block: "nearest" });
      pasteInput.focus();
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

  line = progressLineElement(
    project.goal,
    middle,
    canSelect
      ? (stepId: string) => {
          markSelected(stepId, `Looking at: ${nodeLabel(stepId)}`);
          if (!pasteForm.hidden) updatePasteHint();
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
    const text = projectMapToAscii(
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
  copyRow.appendChild(copyBtn);

  const pasteBtn = document.createElement("button");
  pasteBtn.type = "button";
  pasteBtn.className = "map-copy-button";
  pasteBtn.textContent = "Paste structure";
  pasteBtn.title =
    "Import an outline or ASCII tree (e.g. from another LLM) as steps";
  const pasteForm = document.createElement("form");
  pasteForm.className = "map-paste-form";
  pasteForm.hidden = true;
  const pasteInput = document.createElement("textarea");
  pasteInput.className = "map-paste-input";
  pasteInput.placeholder = "Paste an outline or ASCII tree…";
  pasteInput.rows = 6;
  const pasteHint = document.createElement("p");
  pasteHint.className = "map-paste-hint";
  // Recomputed every time the form opens, not just once at this
  // render pass's construction - markSelected() (e.g. the ⋯ menu's
  // own Paste structure, which selects a node THEN opens this form)
  // changes selectedNodeId without a full re-render, so a value fixed
  // here at build time would otherwise go stale and show the wrong
  // target - see pasteBtn's and the menu's "paste" case below.
  const updatePasteHint = () => {
    pasteHint.textContent = selectedNodeLabel
      ? `Will import under: ${selectedNodeLabel}`
      : "Will import at the project root.";
  };
  updatePasteHint();

  // Preview, not a guess acted on silently: parse_outline() can't tell
  // a throwaway title line from content the user actually wants kept
  // (see its own docstring), so both readings are shown and the user
  // picks - rather than always accepting the parser's positional guess.
  const previewBox = document.createElement("div");
  previewBox.className = "map-paste-preview";
  const previewEmpty = document.createElement("p");
  previewEmpty.className = "map-paste-preview-empty";
  previewEmpty.textContent = "Preview appears here as you type or paste.";
  previewBox.appendChild(previewEmpty);

  const pasteActions = document.createElement("div");
  pasteActions.className = "map-paste-actions";
  const pasteSubmit = document.createElement("button");
  pasteSubmit.type = "submit";
  pasteSubmit.textContent = "Import";
  const pasteCancel = document.createElement("button");
  pasteCancel.type = "button";
  pasteCancel.textContent = "Cancel";
  const pasteError = document.createElement("p");
  pasteError.className = "error";
  pasteError.hidden = true;
  pasteActions.append(pasteSubmit, pasteCancel);
  pasteForm.append(pasteInput, pasteHint, previewBox, pasteActions, pasteError);

  // The working preview tree - every node individually toggleable.
  // Only the single droppable outer title (parse_outline()'s own
  // unwrap condition) starts excluded, matching the default guess;
  // everything else starts included. null until a preview loads.
  let workingTree: PreviewNode[] | null = null;
  let previewSeq = 0;

  const renderPreview = () => {
    previewBox.innerHTML = "";
    if (!workingTree) {
      previewBox.appendChild(previewEmpty);
      return;
    }
    if (applyExclusions(workingTree).length === 0) {
      const none = document.createElement("p");
      none.className = "map-paste-preview-empty";
      none.textContent = "(nothing recognizable yet)";
      previewBox.appendChild(none);
      return;
    }
    previewBox.appendChild(
      previewTreeElement(workingTree, (node) => {
        node.excluded = !node.excluded;
        renderPreview();
      }),
    );
  };

  let previewTimer: number | undefined;
  const schedulePreview = () => {
    window.clearTimeout(previewTimer);
    const text = pasteInput.value.trim();
    if (!text) {
      workingTree = null;
      renderPreview();
      return;
    }
    previewTimer = window.setTimeout(async () => {
      const seq = ++previewSeq;
      try {
        const preview = await previewOutline(text);
        if (seq !== previewSeq) return; // a newer keystroke already fired
        const droppableRoot =
          preview.kept.length === 1 && preview.kept[0].children.length > 0
            ? preview.kept[0]
            : null;
        workingTree = droppableRoot
          ? [toPreviewNode(droppableRoot, true)]
          : preview.kept.map((n) => toPreviewNode(n, false));
        renderPreview();
      } catch {
        if (seq !== previewSeq) return;
        workingTree = null;
        renderPreview();
      }
    }, 300);
  };

  pasteInput.addEventListener("input", schedulePreview);

  pasteBtn.addEventListener("click", () => {
    pasteForm.hidden = !pasteForm.hidden;
    if (!pasteForm.hidden) {
      updatePasteHint();
      pasteInput.focus();
    }
  });
  pasteCancel.addEventListener("click", () => {
    pasteForm.hidden = true;
    pasteInput.value = "";
    pasteError.hidden = true;
    workingTree = null;
    renderPreview();
  });
  pasteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = pasteInput.value.trim();
    if (!text) return;
    pasteError.hidden = true;
    pasteSubmit.disabled = true;
    try {
      // Prefer the edited preview tree (reflects every node the user
      // toggled) over a fresh, unedited re-parse of the raw text -
      // falls back to the text path only if the preview never loaded
      // (e.g. Import clicked before the debounced fetch returned).
      const updated = workingTree
        ? await importProgressionForest(
            project.goal_id,
            applyExclusions(workingTree),
            selectedNodeId,
          )
        : await importProgressionOutline(project.goal_id, text, selectedNodeId);
      pasteInput.value = "";
      pasteForm.hidden = true;
      workingTree = null;
      replaceProject(updated);
    } catch (err) {
      pasteError.hidden = false;
      pasteError.textContent = `(error: ${(err as Error).message})`;
    } finally {
      pasteSubmit.disabled = false;
    }
  });

  copyRow.appendChild(pasteBtn);
  body.appendChild(copyRow);
  body.appendChild(pasteForm);

  // Click empty map space (not a node row) to unselect focus.
  body.addEventListener("click", (event) => {
    // The open paste form's target node IS the current selection - an
    // incidental click on the (now generously padded, see
    // .project-body) empty canvas around it must not silently swap
    // out the import target the user is mid-composing against.
    if (!pasteForm.hidden) return;
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

  fillThread(project.thread ?? [], (stepId, label) => {
    markSelected(stepId, `Looking at: ${label}`);
    if (!pasteForm.hidden) updatePasteHint();
  });
}

function replaceProject(updated: GoalView): void {
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
