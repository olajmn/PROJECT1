/**
 * `/` menu next to Send — pick a slash-command without typing it.
 *
 * Contents
 *  1. Public API
 *      - installCommandMenu()
 */

import { CHAT_COMMANDS } from "./catalog.js";

type CommandMenuOpts = {
  host: HTMLElement;
  input: HTMLTextAreaElement;
};

// 1. Public API

export function installCommandMenu(opts: CommandMenuOpts): void {
  const wrap = document.createElement("div");
  wrap.className = "chat-command-menu";

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "chat-command-menu-toggle";
  toggle.textContent = "/";
  toggle.title = "Commands";
  toggle.setAttribute("aria-haspopup", "listbox");
  toggle.setAttribute("aria-expanded", "false");

  const panel = document.createElement("div");
  panel.className = "chat-command-menu-panel";
  panel.hidden = true;
  panel.setAttribute("role", "listbox");
  panel.setAttribute("aria-label", "Chat commands");

  for (const cmd of CHAT_COMMANDS) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "chat-command-menu-item";
    item.setAttribute("role", "option");
    const slash = document.createElement("span");
    slash.className = "chat-command-menu-slash";
    slash.textContent = cmd.slash;
    const blurb = document.createElement("span");
    blurb.className = "chat-command-menu-blurb";
    blurb.textContent = cmd.blurb;
    item.append(slash, blurb);
    item.addEventListener("click", () => {
      close();
      opts.input.value = `${cmd.slash} `;
      opts.input.dispatchEvent(new Event("input"));
      opts.input.focus();
      const end = opts.input.value.length;
      opts.input.setSelectionRange(end, end);
    });
    panel.appendChild(item);
  }

  const close = (): void => {
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
  };

  const open = (): void => {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
  };

  toggle.addEventListener("click", (event) => {
    event.preventDefault();
    if (panel.hidden) open();
    else close();
  });

  document.addEventListener("click", (event) => {
    if (!wrap.contains(event.target as Node)) close();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });

  wrap.append(toggle, panel);
  opts.host.appendChild(wrap);
}
