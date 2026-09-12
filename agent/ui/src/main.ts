// DOM wiring for the agent/ conversation prototype (free conversation -
// docs/03-architecture.md's "known capability context" path lives on
// active.ts instead, see that file's own docstring). Deliberately one
// small file: appending chat messages and showing an optional
// PlanningNode tree are the whole job here - no framework, no state
// library, no routing beyond the plain <a> links in index.html's nav.
//
// Also shows and lets the user clear cli.py's own Session.
// current_goal_id (GET/POST /api/chat-focus) - otherwise invisible
// state that decides whether the next planning message starts a new
// goal or is read as feedback on whatever goal the chat is currently
// "focused" on. Named "chat focus", not "session" - cli.py's Session
// object happens to hold this AND a separate, persisted Session
// record (see sessions.ts) as two attributes on one object, but
// they're different concepts; renamed from "session" 2026-09-12 once
// both existed side by side and the shared name got confusing. This
// doesn't fix § 5's topic-continuity defect (still nothing detects a
// mid-conversation topic switch) - it only makes the chat's own
// current focus visible and gives a manual way to reset it, and to
// arrive here already pointed at a specific goal (see active.ts's
// "Continue in chat" button).

// Contents
//  1. Chat focus
//      - renderChatFocus()
//      - loadChatFocus()
//  2. Transcript
//      - appendMessage()
//  3. Event listeners
//  4. Initialization

import { fetchChatFocus, sendMessage, setChatFocus } from "./api.js";
import { initNavCounts } from "./nav.js";
import { planElement } from "./tree.js";
import type { ChatFocusView } from "./types.js";

const transcript = document.getElementById("transcript") as HTMLDivElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const chatFocus = document.getElementById("chat-focus") as HTMLDivElement;

// 1. Chat focus

function renderChatFocus(view: ChatFocusView): void {
  chatFocus.innerHTML = "";

  const text = document.createElement("span");
  text.textContent =
    view.goal_id === null
      ? "Chat focus: none - the next planning message starts a new goal."
      : `Chat focus: ${view.goal ?? "(unknown)"} #${view.goal_id}`;
  chatFocus.appendChild(text);

  if (view.goal_id !== null) {
    const clearButton = document.createElement("button");
    clearButton.type = "button";
    clearButton.textContent = "Clear (set_chat_focus)";
    clearButton.className = "clear-chat-focus-button";
    clearButton.addEventListener("click", async () => {
      clearButton.disabled = true;
      try {
        renderChatFocus(await setChatFocus(null));
      } catch (err) {
        clearButton.disabled = false;
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        chatFocus.appendChild(error);
      }
    });
    chatFocus.appendChild(clearButton);
  }
}

function loadChatFocus(): void {
  fetchChatFocus()
    .then(renderChatFocus)
    .catch((err) => {
      chatFocus.textContent = `(error loading chat focus: ${(err as Error).message})`;
    });
}

// 2. Transcript

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

// 3. Event listeners

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
    loadChatFocus();
  } catch (err) {
    appendMessage("Agent", `(error: ${(err as Error).message})`);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

// 4. Initialization

input.focus();
initNavCounts();
loadChatFocus();
