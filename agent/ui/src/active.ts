// The Active page - docs/03-architecture.md's "known capability
// context" path (Part 3 § 3), actually built: each active goal is its
// own card with its own chat, so which goal a message is about is
// never inferred or guessed - it's simply which card the textarea
// belongs to. Talks to /api/goals[/<id>/feedback] (see server.py),
// which runs planning/chat/turn.py (parse in context, route_note,
// LLM1). The Conversation page (index.html/main.ts) is the global
// instance; this is the per-goal one. Continue in chat / chat-focus
// is left as the bridge to that global instance.

// Contents
//  1. Rendering
//      - renderThread()
//      - renderGoalCard()
//  2. Data loading
//      - loadGoals()
//  3. Initialization

import { cancelGoal, fetchActiveGoals, fetchVisions, sendGoalFeedback, setChatFocus, setGoalVision } from "./api.js";
import { initNavCounts } from "./nav.js";
import { planElement } from "./tree.js";
import type { ChatMessage, GoalView, VisionView } from "./types.js";

const list = document.getElementById("goal-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

// 1. Rendering

function renderThread(messages: ChatMessage[]): HTMLElement {
  const thread = document.createElement("div");
  thread.className = "goal-thread";
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
    thread.appendChild(row);
  }
  return thread;
}

function renderGoalCard(goal: GoalView, visions: VisionView[]): HTMLElement {
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

  // Vision link - matches frontend-legacy/templates/active_goal/
  // _goal.html's dropdown: every active (non-archived) Vision, plus
  // "Vision: none" to remove the link, pre-selected to whichever this
  // goal already has.
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
    if (goal.vision_id === vision.id) option.selected = true;
    select.appendChild(option);
  }
  const visionButton = document.createElement("button");
  visionButton.type = "submit";
  visionButton.textContent = "Update vision (set_goal_vision)";
  visionForm.append(select, visionButton);

  visionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const raw = select.value;
    select.disabled = true;
    visionButton.disabled = true;
    try {
      const updated = await setGoalVision(goal.goal_id, raw ? Number(raw) : null);
      card.replaceWith(renderGoalCard(updated, visions));
    } catch (err) {
      select.disabled = false;
      visionButton.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      visionForm.appendChild(error);
    }
  });

  card.appendChild(visionForm);

  card.appendChild(renderThread(goal.thread ?? []));

  if (goal.node) {
    card.appendChild(planElement(goal.node));
  }

  const form = document.createElement("form");
  form.className = "feedback-form";
  const textarea = document.createElement("textarea");
  textarea.rows = 2;
  textarea.placeholder = "Reply...";
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
      card.replaceWith(renderGoalCard(updated, visions));
      // Feedback can mark a goal completed, moving it off this list -
      // the nav badges need to reflect that too.
      initNavCounts();
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

  // Two actions on the goal itself, not part of the plan/feedback flow
  // above - kept as their own element after the feedback form, same
  // placement frontend-legacy/templates/active_goal/_cancel.html used
  // for Cancel. No confirmation step on either, matching that
  // precedent.
  const actions = document.createElement("div");
  actions.className = "card-actions";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.textContent = "Cancel goal (cancel_goal)";
  cancelButton.className = "cancel-button";
  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await cancelGoal(goal.goal_id);
      card.remove();
      empty.hidden = list.childElementCount > 0;
      initNavCounts();
    } catch (err) {
      cancelButton.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      card.appendChild(error);
    }
  });
  actions.appendChild(cancelButton);

  // The manual bridge to the free-conversation path: points cli.py's
  // own Session.current_goal_id ("chat focus", otherwise invisible,
  // only ever guessed at) at this goal, then sends the browser to
  // Conversation to continue there - see main.ts's own chat-focus bar.
  const continueButton = document.createElement("button");
  continueButton.type = "button";
  continueButton.textContent = "Continue in chat (set_chat_focus)";
  continueButton.className = "continue-chat-button";
  continueButton.addEventListener("click", async () => {
    continueButton.disabled = true;
    try {
      await setChatFocus(goal.goal_id);
      window.location.href = "index.html";
    } catch (err) {
      continueButton.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      card.appendChild(error);
    }
  });
  actions.appendChild(continueButton);

  card.appendChild(actions);

  return card;
}

// 2. Data loading

async function loadGoals(): Promise<void> {
  const [goals, allVisions] = await Promise.all([fetchActiveGoals(), fetchVisions()]);
  const visions = allVisions.filter((v) => !v.archived);
  list.innerHTML = "";
  empty.hidden = goals.length > 0;
  for (const goal of goals) {
    list.appendChild(renderGoalCard(goal, visions));
  }
}

// 3. Initialization

loadGoals().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading goals: ${(err as Error).message})`;
});
initNavCounts();
