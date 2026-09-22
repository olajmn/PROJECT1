/**
 * Create pane — naming and minting a project. Mirrors
 * backend/project/panes/create/, which owns the same concern server side.
 *
 * The panel renders in the middle column, but it is not the canvas: the
 * column shows Create when there is no canvas to show, or when the
 * sidebar's "+" asks for it over an open project.
 *
 * Empty name → Spotify-style autoname (`New project N`) via autoname.ts.
 */

import { createGoal } from "../api.js";
import { setButtonBusy } from "../shell/busy.js";
import { getActiveUserId } from "../user/activeUser.js";
import type { ProjectView } from "../types.js";
import { nextNewProjectName } from "./autoname.js";

export type CreatePanelHandle = {
  /** True while the panel should take the middle pane. */
  isOpen: () => boolean;
  /** Put the panel in `host` and focus the field. */
  mount: (host: HTMLElement) => void;
  /** Leave the panel — the caller re-renders back to its project. */
  close: () => void;
};

type CreatePanelOpts = {
  /** No id picked yet, so nothing can own the project. */
  onNeedUser: () => void;
  onCreated: (project: ProjectView) => void;
  /** Re-render the workspace after the panel opens or closes. */
  onChange: () => void;
  /** Existing titles (active id) — used for autoname. */
  getTitles: () => string[];
};

export function installCreatePanel(opts: CreatePanelOpts): CreatePanelHandle {
  const openBtn = document.getElementById("create-open") as HTMLButtonElement;
  const panel = document.getElementById("create-panel") as HTMLElement;
  const form = document.getElementById("create-form") as HTMLFormElement;
  const input = document.getElementById("create-input") as HTMLTextAreaElement;
  const error = document.getElementById("create-error") as HTMLParagraphElement;
  const submit = form.querySelector(
    'button[type="submit"]',
  ) as HTMLButtonElement;
  const bare = document.getElementById("create-bare") as HTMLButtonElement;

  let open = false;

  openBtn.addEventListener("click", () => {
    open = true;
    opts.onChange();
  });

  /** `planned` false mints a named project and leaves the tree empty. */
  const mint = async (
    busyBtn: HTMLButtonElement,
    planned: boolean,
  ): Promise<void> => {
    const typed = input.value.trim();
    const text = typed || nextNewProjectName(opts.getTitles());

    const userId = getActiveUserId();
    if (userId === null) {
      error.hidden = false;
      error.textContent =
        "(pick or create an id — click the label at the top of the sidebar)";
      opts.onNeedUser();
      return;
    }

    input.disabled = true;
    setButtonBusy(busyBtn, true);
    error.hidden = true;
    try {
      const created = await createGoal(text, userId, planned);
      input.value = "";
      open = false;
      opts.onCreated(created);
    } catch (err) {
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    } finally {
      input.disabled = false;
      setButtonBusy(busyBtn, false);
    }
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void mint(submit, true);
  });

  bare.addEventListener("click", () => {
    void mint(bare, false);
  });

  return {
    isOpen: () => open,

    mount: (host: HTMLElement) => {
      host.appendChild(panel);
      panel.hidden = false;
      input.focus();
    },

    close: () => {
      open = false;
    },
  };
}
