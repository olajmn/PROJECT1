// DOM wiring for the agent/ conversation prototype (free conversation -
// docs/03-architecture.md's "known capability context" path lives on
// active.ts instead, see that file's own docstring). Deliberately one
// small file: appending chat messages and showing an optional
// PlanningNode tree are the whole job here - no framework, no state
// library, no routing beyond the plain <a> links in index.html's nav.

import { sendMessage } from "./api.js";
import { initNavCounts } from "./nav.js";
import { planElement } from "./tree.js";

const transcript = document.getElementById("transcript") as HTMLDivElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;

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
  } catch (err) {
    appendMessage("Agent", `(error: ${(err as Error).message})`);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

input.focus();
initNavCounts();
