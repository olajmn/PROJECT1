// One chat message row: "You" / "Agent" label + text.
// Shared by Projects (via isolateChat) and other chat surfaces.

import type { ChatMessage } from "../types.js";

export function messageRow(
  message: Pick<ChatMessage, "role" | "text">,
): HTMLDivElement {
  const row = document.createElement("div");
  row.className = `message message-${message.role === "user" ? "you" : "agent"}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = message.role === "user" ? "You" : "Agent";
  const body = document.createElement("span");
  body.className = "text";
  body.textContent = message.text;
  row.append(label, body);
  return row;
}
