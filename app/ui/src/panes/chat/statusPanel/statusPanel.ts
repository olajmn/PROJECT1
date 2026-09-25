// The Status panel above the chat: where the project stands now and what
// has happened (backend/project/status/). The chat's model gets the same
// text, so what you see here is what it knows.
//
// The "Status" button opens and closes it; open/closed and the height are
// remembered across projects (localStorage).
//
// Contents
//  1. Types
//      - StatusPanel
//  2. Public API
//      - createStatusPanel()

import type { ProjectStatus } from "../../../dataShapes.js";
import { applyStoredPanelHeight, installPanelResize } from "./resizePanel.js";
import { drawStatus } from "./drawStatus.js";

const OPEN_KEY = "projects.statusOpen";

// 1. Types

export type StatusPanel = {
  /** Show one project's status. `onNode` runs when a node name is clicked. */
  fill: (status: ProjectStatus | null, onNode: (label: string) => void) => void;
};

// 2. Public API

export function createStatusPanel(
  panel: HTMLElement,
  handle: HTMLElement,
  toggle: HTMLButtonElement,
): StatusPanel {
  installPanelResize(panel, handle);

  let lastStatus: ProjectStatus | null = null;
  let lastOnNode: ((label: string) => void) | null = null;
  let open = readOpen();

  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    open = !open;
    rememberOpen(open);
    paint();
  });

  function paint(): void {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.classList.toggle("is-active", open);
    panel.innerHTML = "";
    panel.hidden = !open;
    handle.hidden = !open;
    if (!open) return;
    if (!lastStatus || lastStatus.summary.length === 0 || !lastOnNode) {
      // Keep the pinned height with nothing to show, so the handle stays usable.
      applyStoredPanelHeight(panel, { clampToContent: false });
      return;
    }
    panel.appendChild(drawStatus(lastStatus, lastOnNode));
    applyStoredPanelHeight(panel);
  }

  return {
    fill: (status, onNode) => {
      lastStatus = status;
      lastOnNode = onNode;
      paint();
    },
  };
}

/** Open unless the user closed it before. */
function readOpen(): boolean {
  try {
    return localStorage.getItem(OPEN_KEY) !== "0";
  } catch {
    return true;
  }
}

function rememberOpen(next: boolean): void {
  try {
    localStorage.setItem(OPEN_KEY, next ? "1" : "0");
  } catch {
    /* private mode / quota — open state is best-effort */
  }
}
