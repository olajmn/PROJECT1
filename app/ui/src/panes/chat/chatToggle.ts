// The chat show / hide button. It lives on its own layer over the columns,
// pinned to the block's top-right corner (css/panes/chat/chatToggle.css), so it
// stays in the same place whether the chat is open or collapsed: over the
// right end of the chat's top strip, or of the map's when the chat is
// away. Open vs closed is drawn by CSS from .workspace.is-chat-collapsed:
// a filled bubble while the chat is open, a hollow one while collapsed.

import { setTip } from "../../shell/tip.js";

export function installChatToggle(
  workspace: HTMLElement,
  onToggle: () => void,
): void {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "chat-toggle";
  setTip(button, "Show or hide chat", "below", "end");
  button.innerHTML =
    '<svg width="15" height="15" viewBox="0 0 24 24" stroke="currentColor" ' +
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M5 5h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H10l-5 4V6a1 1 0 0 1 1-1z"/></svg>';
  button.addEventListener("click", onToggle);
  workspace.appendChild(button);
}
