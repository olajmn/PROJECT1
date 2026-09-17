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
  removeProgressionStep,
  sendGoalFeedback,
  setGoalVision,
  zoomGoalStep,
} from "./api.js";
import { progressLineElement } from "./tree.js";
import type { ChatMessage, GoalView, PlanningNode, VisionView } from "./types.js";

const createForm = document.getElementById("create-form") as HTMLFormElement;
const createInput = document.getElementById("create-input") as HTMLTextAreaElement;
const createError = document.getElementById("create-error") as HTMLParagraphElement;
const projectList = document.getElementById("project-list") as HTMLDivElement;
const listEmpty = document.getElementById("list-empty") as HTMLParagraphElement;
const projectMain = document.getElementById("project-main") as HTMLElement;
const mainEmpty = document.getElementById("main-empty") as HTMLParagraphElement;
const projectChat = document.getElementById("project-chat") as HTMLElement;
const chatThread = document.getElementById("chat-thread") as HTMLDivElement;
const chatForm = document.getElementById("chat-form") as HTMLFormElement;
const chatInput = document.getElementById("chat-input") as HTMLTextAreaElement;
const chatError = document.getElementById("chat-error") as HTMLParagraphElement;

const PROGRESSION_STEP_ID = /^p\d+$/;

let projects: GoalView[] = [];
let visions: VisionView[] = [];
let selectedId: number | null = null;

function findNode(node: PlanningNode, id: string): PlanningNode | null {
  if (node.id === id) return node;
  for (const child of node.children) {
    const found = findNode(child, id);
    if (found) return found;
  }
  return null;
}

function isProgressionTree(node: PlanningNode): boolean {
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
      renderList();
      renderWorkspace();
    });
    projectList.appendChild(button);
  }
}

function fillThread(messages: ChatMessage[]): void {
  chatThread.innerHTML = "";
  for (const message of messages) {
    const row = document.createElement("div");
    row.className = `message message-${message.role === "user" ? "you" : "agent"}`;
    const label = document.createElement("span");
    label.className = "who";
    label.textContent = message.role === "user" ? "You" : "Agent";
    const body = document.createElement("span");
    body.className = "text";
    body.textContent = message.text;
    row.append(label, body);
    chatThread.appendChild(row);
  }
  chatThread.scrollTop = chatThread.scrollHeight;
}

function renderWorkspace(): void {
  const project = selected();
  projectMain.innerHTML = "";
  chatError.hidden = true;

  if (!project) {
    projectMain.appendChild(mainEmpty);
    mainEmpty.hidden = false;
    projectChat.hidden = true;
    return;
  }

  mainEmpty.hidden = true;
  projectChat.hidden = false;

  const body = document.createElement("div");
  body.className = "project-body";

  const header = document.createElement("div");
  header.className = "card-header";
  const title = document.createElement("h1");
  title.className = "project-title";
  title.textContent = project.goal;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${project.goal_id}`;
  header.append(title, id);
  body.appendChild(header);

  if (project.surface) {
    const surface = document.createElement("p");
    surface.className = "project-surface";
    surface.textContent = project.surface;
    body.appendChild(surface);
  }

  // Progress line: Start — (optional middle steps) — End.
  // Middle comes from progression children when present.
  // + lets the user name a bead (no LLM) — steers the map.
  const middle = project.node?.children ?? [];
  const canZoom = project.node ? isProgressionTree(project.node) : false;
  let line: HTMLDivElement;
  const addBead = async (trimmed: string) => {
    line.classList.add("plan-busy");
    try {
      const updated = await addProgressionStep(project.goal_id, trimmed);
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
      replaceProject(updated);
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
    canZoom
      ? async (stepId: string) => {
          line.classList.add("plan-busy");
          try {
            const updated = await zoomGoalStep(project.goal_id, stepId);
            const before = project.node ? findNode(project.node, stepId) : null;
            const after = updated.node ? findNode(updated.node, stepId) : null;
            const grew =
              (after?.children.length ?? 0) > (before?.children.length ?? 0);
            replaceProject(updated);
            if (!grew) {
              const note = document.createElement("p");
              note.className = "zoom-note";
              note.textContent =
                "Already fine enough to act on — nothing more under that step.";
              projectMain.querySelector(".progress-line")?.appendChild(note);
            }
          } catch (err) {
            line.classList.remove("plan-busy");
            const error = document.createElement("p");
            error.className = "error";
            error.textContent = `(error: ${(err as Error).message})`;
            line.appendChild(error);
          }
        }
      : undefined,
    addBead,
    removeBead,
  );
  body.appendChild(line);

  if (!project.node) {
    const hint = document.createElement("p");
    hint.className = "project-hint";
    hint.textContent =
      "Add steps with +, or talk — a plan from the agent is optional.";
    body.appendChild(hint);
  }

  projectMain.appendChild(body);

  // Meta controls sit at the bottom of the column (same idea as the
  // chat compose strip) — not competing with the map.
  const footer = document.createElement("div");
  footer.className = "project-footer";

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
  footer.appendChild(visionForm);

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
      footer.appendChild(error);
    }
  });
  actions.appendChild(cancelButton);
  footer.appendChild(actions);
  projectMain.appendChild(footer);

  fillThread(project.thread ?? []);
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
    const updated = await sendGoalFeedback(project.goal_id, text);
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
