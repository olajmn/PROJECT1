/**
 * Create pane — naming and minting a project. Mirrors
 * backend/project/panes/create/, which owns the same concern server side.
 *
 * The panel renders in the middle column, but it is not the canvas: the
 * column shows Create when there is no canvas to show, or when the
 * sidebar's "+" asks for it over an open project.
 *
 * Empty name → Spotify-style autoname (`New project N`) via defaultNames.ts.
 * Add folder mints empty, then walks the same import as the map.
 */

import { createProject } from "../../api.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import { getActiveUserId } from "../../user/activeAccount.js";
import type { ProjectView } from "../../dataShapes.js";
import { mintFromFolder } from "./projectFromFolder.js";
import { nextNewProjectName } from "./defaultNames.js";

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
  const heading = document.getElementById("create-heading") as HTMLParagraphElement;
  const form = document.getElementById("create-form") as HTMLFormElement;
  const input = document.getElementById("create-input") as HTMLTextAreaElement;
  const error = document.getElementById("create-error") as HTMLParagraphElement;
  const submit = document.getElementById("create-bare") as HTMLButtonElement;
  const folderBtn = document.getElementById("create-folder") as HTMLButtonElement;

  let open = false;

  openBtn.addEventListener("click", () => {
    open = true;
    if (getActiveUserId() !== null) {
      error.hidden = true;
      error.textContent = "";
    }
    opts.onChange();
  });

  /** Name + empty canvas. No engine. */
  const mint = async (): Promise<void> => {
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
    setButtonBusy(submit, true);
    error.hidden = true;
    try {
      const created = await createProject(text, userId);
      input.value = "";
      open = false;
      opts.onCreated(created);
    } catch (err) {
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    } finally {
      input.disabled = false;
      setButtonBusy(submit, false);
    }
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void mint();
  });

  folderBtn.addEventListener("click", () => {
    void addFolder();
  });

  const addFolder = async (): Promise<void> => {
    const userId = getActiveUserId();
    if (userId === null) {
      error.hidden = false;
      error.textContent =
        "(pick or create an id — click the label at the top of the sidebar)";
      opts.onNeedUser();
      return;
    }
    setButtonBusy(folderBtn, true);
    error.hidden = true;
    try {
      const created = await mintFromFolder({
        typedName: input.value,
        titles: opts.getTitles(),
        userId,
      });
      if (!created) return;
      input.value = "";
      open = false;
      opts.onCreated(created);
    } catch (err) {
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    } finally {
      setButtonBusy(folderBtn, false);
    }
  };

  return {
    isOpen: () => open,

    mount: (host: HTMLElement) => {
      host.appendChild(panel);
      panel.hidden = false;
      heading.textContent =
        getActiveUserId() === null
          ? "Pick or create an id above, then name a project."
          : "Name a new project.";
      // Drop a stale "pick an id" error once an id is active again.
      if (getActiveUserId() !== null) {
        error.hidden = true;
        error.textContent = "";
      }
      input.focus();
    },

    close: () => {
      open = false;
    },
  };
}
