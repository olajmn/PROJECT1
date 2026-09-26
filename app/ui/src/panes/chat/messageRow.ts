// One chat message row: "You" / "Agent" label, the text, and — when the
// message has a time — a small time under it, like a messaging app.
// Shared by the Projects chat (via showOnlyThis).

import type { ChatMessage } from "../../dataShapes.js";

export function messageRow(
  message: Pick<ChatMessage, "role" | "text" | "at">,
): HTMLDivElement {
  const row = document.createElement("div");
  row.className = `message message-${message.role === "user" ? "you" : "agent"}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = message.role === "user" ? "You" : "Agent";
  const body = document.createElement("div");
  body.className = "body";
  const text = document.createElement("span");
  text.className = "text";
  text.textContent = message.text;
  body.append(text);
  const when = message.at ? new Date(message.at) : null;
  if (when && !Number.isNaN(when.getTime())) {
    const time = document.createElement("time");
    time.className = "when";
    time.dateTime = message.at!;
    time.textContent = shortTime(when);
    time.title = when.toLocaleString();
    body.append(time);
  }
  row.append(label, body);
  return row;
}

/** "20:27" today, "25 Sep 20:27" earlier this year, with the year before that. */
function shortTime(when: Date): string {
  const now = new Date();
  const clock = when.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  if (when.toDateString() === now.toDateString()) return clock;
  const day = when.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    ...(when.getFullYear() === now.getFullYear() ? {} : { year: "numeric" }),
  });
  return `${day} ${clock}`;
}
