// The Current state panel above the chat: where the project stands now
// and what has happened (backend/project/status/). The chat's model gets
// the same summary rows and the changes themselves, not the per-day
// counts; a selected day gives it that day's changes.
//
// The "Current state" button opens and closes it; open/closed and the
// height are remembered across projects (localStorage).
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
  /** Show one project's status. `onNode` runs when a node name is
   * clicked, `onDay` when a day is picked (null lets it go). */
  fill: (
    status: ProjectStatus | null,
    onNode: (label: string) => void,
    selectedDay?: string | null,
    onDay?: (day: string | null) => void,
  ) => void;
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
  let lastSelectedDay: string | null = null;
  let lastOnDay: (day: string | null) => void = () => {};
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
    panel.appendChild(drawStatus(lastStatus, lastOnNode, lastSelectedDay, lastOnDay));
    applyStoredPanelHeight(panel);
  }

  return {
    fill: (status, onNode, selectedDay = null, onDay = () => {}) => {
      lastStatus = status;
      lastOnNode = onNode;
      lastSelectedDay = selectedDay;
      lastOnDay = onDay;
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
