// The Vision page - create, list, and archive a Vision (broader,
// cross-goal context a Goal can optionally reference - see
// docs/planning-model.md, the authority on Vision), plus, for each
// Vision, which active goals are currently linked to it - the reverse
// of active.ts's own Vision-link dropdown (that's where the link is
// made/changed, not here). Active and archived shown as two separate
// sections, same split frontend-legacy/templates/vision/page.html
// already established; each Vision's linked goals shown the same way
// _vision_form.html's group_goals_by_vision_id() did - only active
// goals (completed isn't wired into this relation), unaffected by the
// Vision itself being archived.

import { archiveVision, createVision, fetchActiveGoals, fetchVisions } from "./api.js";
import { initNavCounts } from "./nav.js";
import type { GoalView, VisionView } from "./types.js";

const activeList = document.getElementById("active-visions") as HTMLDivElement;
const archivedList = document.getElementById("archived-visions") as HTMLDivElement;
const emptyActive = document.getElementById("empty-active") as HTMLParagraphElement;
const emptyArchived = document.getElementById("empty-archived") as HTMLParagraphElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;

function renderVisionCard(vision: VisionView, goals: GoalView[]): HTMLElement {
  const card = document.createElement("article");
  card.className = "vision-card";

  const top = document.createElement("div");
  top.className = "vision-card-top";

  const header = document.createElement("div");
  header.className = "card-header";
  const text = document.createElement("p");
  text.textContent = vision.text;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${vision.id}`;
  header.append(text, id);
  top.appendChild(header);

  if (!vision.archived) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Archive";
    button.className = "archive-button";
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await archiveVision(vision.id);
        await loadVisions();
        initNavCounts();
      } catch (err) {
        button.disabled = false;
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        card.appendChild(error);
      }
    });
    top.appendChild(button);
  }

  card.appendChild(top);

  const group = document.createElement("div");
  group.className = "goal-group";
  if (goals.length === 0) {
    const emptyState = document.createElement("p");
    emptyState.className = "empty-state";
    emptyState.textContent = "(no Goals yet)";
    group.appendChild(emptyState);
  } else {
    for (const goal of goals) {
      const item = document.createElement("div");
      item.className = "goal-group-item";
      const goalText = document.createElement("span");
      goalText.textContent = goal.goal;
      const goalId = document.createElement("span");
      goalId.className = "entity-id";
      goalId.textContent = `#${goal.goal_id}`;
      item.append(goalText, goalId);
      group.appendChild(item);
    }
  }
  card.appendChild(group);

  return card;
}

async function loadVisions(): Promise<void> {
  const [visions, goals] = await Promise.all([fetchVisions(), fetchActiveGoals()]);
  const goalsByVision = new Map<number, GoalView[]>();
  for (const goal of goals) {
    if (goal.vision_id === null) continue;
    const linked = goalsByVision.get(goal.vision_id) ?? [];
    linked.push(goal);
    goalsByVision.set(goal.vision_id, linked);
  }

  const active = visions.filter((v) => !v.archived);
  const archived = visions.filter((v) => v.archived);

  activeList.innerHTML = "";
  emptyActive.hidden = active.length > 0;
  for (const vision of active) {
    activeList.appendChild(renderVisionCard(vision, goalsByVision.get(vision.id) ?? []));
  }

  archivedList.innerHTML = "";
  emptyArchived.hidden = archived.length > 0;
  for (const vision of archived) {
    archivedList.appendChild(renderVisionCard(vision, goalsByVision.get(vision.id) ?? []));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.disabled = true;
  try {
    await createVision(text);
    input.value = "";
    await loadVisions();
    initNavCounts();
  } catch (err) {
    const error = document.createElement("p");
    error.className = "error";
    error.textContent = `(error: ${(err as Error).message})`;
    form.appendChild(error);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

loadVisions().catch((err) => {
  emptyActive.hidden = false;
  emptyActive.textContent = `(error loading visions: ${(err as Error).message})`;
});
initNavCounts();
