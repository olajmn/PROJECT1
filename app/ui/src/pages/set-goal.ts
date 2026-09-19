// The Set Goal page - starting something genuinely new. Posts to
// /api/goals (skips Node 1/2/3, same as Projects' feedback path), then
// sends the browser to Projects to see the result.
//
// Below the form, a plain list of every active goal's text and id —
// an overview to orient among existing goals without opening a full
// Projects workspace. Reuses GET /api/goals (projects.ts's own data
// source), just rendered as single lines instead of the map shell.

// Contents
//  1. Rendering
//      - renderGoalLine()
//  2. Data loading
//      - loadGoals()
//  3. Event listeners
//  4. Initialization

import { createGoal, fetchActiveGoals } from "../api.js";
import { initVisionCount } from "../visionCount.js";
import type { GoalView } from "../types.js";

const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const button = form.querySelector("button") as HTMLButtonElement;
const error = document.getElementById("error") as HTMLParagraphElement;
const list = document.getElementById("goal-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

// 1. Rendering

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

// 2. Data loading

async function loadGoals(): Promise<void> {
  const goals = await fetchActiveGoals();
  list.innerHTML = "";
  empty.hidden = goals.length > 0;
  for (const goal of goals) {
    list.appendChild(renderGoalLine(goal));
  }
}

// 3. Event listeners

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  input.disabled = true;
  button.disabled = true;
  error.hidden = true;

  try {
    const created = await createGoal(text);
    window.location.href = `projects.html?id=${created.goal_id}`;
  } catch (err) {
    input.disabled = false;
    button.disabled = false;
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
});

// 4. Initialization

input.focus();
loadGoals().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading goals: ${(err as Error).message})`;
});
initVisionCount();
