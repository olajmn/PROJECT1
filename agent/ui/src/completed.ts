// The Completed page - read-only, unlike Active's cards: a completed
// goal doesn't take new feedback (see planner.py - there is no
// "un-complete" or continue-after-completion path), so this only
// shows what was already decided, same GoalView shape and
// planElement() Active uses, minus the feedback form.

import { fetchCompletedGoals } from "./api.js";
import { planElement } from "./tree.js";
import type { GoalView } from "./types.js";

const list = document.getElementById("goal-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

function renderGoalCard(goal: GoalView): HTMLElement {
  const card = document.createElement("article");
  card.className = "goal-card";

  const header = document.createElement("div");
  header.className = "card-header";
  const title = document.createElement("h2");
  title.textContent = goal.goal;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${goal.goal_id}`;
  header.append(title, id);
  card.appendChild(header);

  if (goal.surface) {
    const surface = document.createElement("p");
    surface.className = "surface";
    surface.textContent = goal.surface;
    card.appendChild(surface);
  }

  if (goal.node) {
    card.appendChild(planElement(goal.node));
  }

  return card;
}

async function loadGoals(): Promise<void> {
  const goals = await fetchCompletedGoals();
  list.innerHTML = "";
  empty.hidden = goals.length > 0;
  for (const goal of goals) {
    list.appendChild(renderGoalCard(goal));
  }
}

loadGoals().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading goals: ${(err as Error).message})`;
});
