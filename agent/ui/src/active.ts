// The Active page - docs/03-architecture.md's "known capability
// context" path (Part 3 § 3), actually built: each active goal is its
// own card with its own feedback box, so which goal a message is
// about is never inferred or guessed - it's simply which card the
// textarea belongs to. Talks to /api/goals[/<id>/feedback] (see
// server.py's own docstring for why those skip Node 1/2/3 entirely),
// never /api/message - this page has no free-conversation box of its
// own; that's what the Conversation page (index.html/main.ts) is for.

import { cancelGoal, fetchActiveGoals, sendGoalFeedback } from "./api.js";
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

  const form = document.createElement("form");
  form.className = "feedback-form";
  const textarea = document.createElement("textarea");
  textarea.rows = 2;
  textarea.placeholder = "How's it going?";
  textarea.required = true;
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Send";
  form.append(textarea, button);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = textarea.value.trim();
    if (!text) return;
    textarea.disabled = true;
    button.disabled = true;
    try {
      const updated = await sendGoalFeedback(goal.goal_id, text);
      card.replaceWith(renderGoalCard(updated));
    } catch (err) {
      textarea.disabled = false;
      button.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      form.appendChild(error);
    }
  });

  card.appendChild(form);

  // An action on the goal itself, not part of the plan/feedback flow
  // above - kept as its own element after the feedback form, same
  // placement frontend-legacy/templates/active_goal/_cancel.html used.
  // No confirmation step, matching that same precedent.
  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = "Cancel goal";
  cancelButton.className = "cancel-button";
  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await cancelGoal(goal.goal_id);
      card.remove();
      empty.hidden = list.childElementCount > 0;
    } catch (err) {
      cancelButton.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      card.appendChild(error);
    }
  });
  card.appendChild(cancelButton);

  return card;
}

async function loadGoals(): Promise<void> {
  const goals = await fetchActiveGoals();
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
