/**
 * Greys the leading slash-command in the chat box when it matches a
 * known command (`/add`, `/select`, `/project_summary`, aliases).
 *
 * A textarea cannot style part of its text, so a mirror behind it
 * shows the grey token while the real field stays transparent.
 */

import { matchCommandPrefix } from "./catalog.js";

export function installCommandHighlight(input: HTMLTextAreaElement): void {
  const parent = input.parentElement;
  if (!parent) return;

  const shell = document.createElement("div");
  shell.className = "chat-input-shell";
  const mirror = document.createElement("div");
  mirror.className = "chat-input-mirror";
  mirror.setAttribute("aria-hidden", "true");

  parent.insertBefore(shell, input);
  shell.append(mirror, input);
  input.classList.add("chat-input-overlay");

  const paint = (): void => {
    const value = input.value;
    mirror.replaceChildren();
    const matched = matchCommandPrefix(value);
    if (!matched) {
      mirror.append(document.createTextNode(value));
      return;
    }
    const cmd = document.createElement("span");
    cmd.className = "chat-input-command";
    cmd.textContent = matched.token;
    mirror.append(cmd, document.createTextNode(matched.rest));
  };

  const syncScroll = (): void => {
    mirror.scrollTop = input.scrollTop;
    mirror.scrollLeft = input.scrollLeft;
  };

  input.addEventListener("input", paint);
  input.addEventListener("scroll", syncScroll);
  paint();
}
