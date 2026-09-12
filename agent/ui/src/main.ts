// DOM wiring for the agent/ conversation prototype (free conversation -
// docs/03-architecture.md's "known capability context" path lives on
// active.ts instead, see that file's own docstring). Deliberately one
// small file: appending chat messages and showing an optional
// PlanningNode tree are the whole job here - no framework, no state
// library, no routing beyond the plain <a> links in index.html's nav.
//
// Also shows and lets the user clear cli.py's own Session.
// current_goal_id (GET/POST /api/session) - otherwise invisible state
// that decides whether the next planning message starts a new goal or
// is read as feedback on whatever goal the session already has. This
// doesn't fix § 5's topic-continuity defect (still nothing detects a
// mid-conversation topic switch) - it only makes the session's own
// current state visible and gives a manual way to reset it, and to
// arrive here already pointed at a specific goal (see active.ts's
// "Continue in chat" button).

import { fetchSession, sendMessage, setSession } from "./api.js";
import { initNavCounts } from "./nav.js";
import { planElement } from "./tree.js";
import type { SessionView } from "./types.js";

const transcript = document.getElementById("transcript") as HTMLDivElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const sessionInfo = document.getElementById("session-info") as HTMLDivElement;

function renderSessionInfo(view: SessionView): void {
  sessionInfo.innerHTML = "";

  const text = document.createElement("span");
  text.textContent =
    view.goal_id === null
      ? "Session goal: none - the next planning message starts a new goal."
      : `Session goal: ${view.goal ?? "(unknown)"} #${view.goal_id}`;
  sessionInfo.appendChild(text);

  if (view.goal_id !== null) {
    const clearButton = document.createElement("button");
    clearButton.type = "button";
    clearButton.textContent = "Clear (set_session)";
    clearButton.className = "clear-session-button";
    clearButton.addEventListener("click", async () => {
      clearButton.disabled = true;
      try {
        renderSessionInfo(await setSession(null));
      } catch (err) {
        clearButton.disabled = false;
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        sessionInfo.appendChild(error);
      }
    });
    sessionInfo.appendChild(clearButton);
  }
}

function loadSession(): void {
  fetchSession()
    .then(renderSessionInfo)
    .catch((err) => {
      sessionInfo.textContent = `(error loading session: ${(err as Error).message})`;
    });
}

function appendMessage(who: "You" | "Agent", text: string): void {
  const row = document.createElement("div");
  row.className = `message message-${who.toLowerCase()}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who;
  const body = document.createElement("span");
  body.className = "text";
  body.textContent = text;
  row.append(label, body);
  transcript.appendChild(row);
  transcript.scrollTop = transcript.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage("You", text);
  input.value = "";
  input.disabled = true;

  try {
    const result = await sendMessage(text);
    appendMessage("Agent", result.reply);
    if (result.node) {
      transcript.appendChild(planElement(result.node));
      transcript.scrollTop = transcript.scrollHeight;
    }
    loadSession();
  } catch (err) {
    appendMessage("Agent", `(error: ${(err as Error).message})`);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

input.focus();
initNavCounts();
loadSession();
