// The Set Goal page - the explicit action Active's cards can't be:
// starting something genuinely new. Posts to /api/goals (see
// server.py's own docstring - skips Node 1/2/3, same as Active's
// feedback path), then sends the browser to Active to see the result
// as a card, rather than showing it inline here.
//
// Below the form, a plain list of every active goal's text and id -
// same purpose and shape as frontend-legacy/templates/set_goal/
// _goal_list.html: an overview to orient among existing goals without
// opening Active's full cards (plan tree, feedback form). Reuses
// GET /api/goals (active.ts's own data source), just rendered as
// single lines instead of cards.

// Contents
//  1. Rendering
//      - renderGoalLine()
//  2. Data loading
//      - loadGoals()
//  3. Event listeners
//  4. Initialization

import { createGoal, fetchActiveGoals } from "./api.js";
import { initNavCounts } from "./nav.js";
import type { GoalView } from "./types.js";

const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const button = form.querySelector("button") as HTMLButtonElement;
const error = document.getElementById("error") as HTMLParagraphElement;
const list = document.getElementById("goal-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

function renderGoalLine(goal: GoalView): HTMLElement {
  const line = document.createElement("div");
  line.className = "goal-line";
  const text = document.createElement("span");
  text.textContent = goal.goal;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${goal.goal_id}`;
  line.append(text, id);
  return line;
}

async function loadGoals(): Promise<void> {
  const goals = await fetchActiveGoals();
  list.innerHTML = "";
  empty.hidden = goals.length > 0;
  for (const goal of goals) {
    list.appendChild(renderGoalLine(goal));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  input.disabled = true;
  button.disabled = true;
  error.hidden = true;

  try {
    await createGoal(text);
    window.location.href = "active.html";
  } catch (err) {
    input.disabled = false;
    button.disabled = false;
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
});

input.focus();
loadGoals().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading goals: ${(err as Error).message})`;
});
initNavCounts();
