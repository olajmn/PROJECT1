// The bar under the map: Copy as ASCII, Paste structure, Add folder,
// Archive. (Project summary is Talk `/project_summary` — see chat/commands.)

// Contents
//  1. Types
//  2. Public API
//      - mountBottomBar()

import { archiveProject } from "../../api.js";
import { displayProjectTitle } from "../create/defaultNames.js";
import { copyAsText } from "./copyAsText.js";
import { buildAddFolderPanel } from "./folderForm.js";
import { buildPasteTreePanel } from "./pasteForm.js";
import type { MapNode, ProjectView } from "../../dataShapes.js";

// 1. Types

export type BottomBar = {
  copyRow: HTMLDivElement;
  pasteForm: HTMLElement;
  folderForm: HTMLElement;
  paste: ReturnType<typeof buildPasteTreePanel>;
  folder: ReturnType<typeof buildAddFolderPanel>;
};

type BottomBarOpts = {
  project: ProjectView;
  middle: MapNode[];
  getSelectedNodeId: () => string | null;
  getSelectedNodeLabel: () => string | null;
  onUpdated: (updated: ProjectView) => void;
  onArchived: () => void;
};

// 2. Public API

export function mountBottomBar(opts: BottomBarOpts): BottomBar {
  const { project, middle } = opts;

  const paste = buildPasteTreePanel({
    getParentLabel: () => opts.getSelectedNodeLabel(),
    getParentId: () => opts.getSelectedNodeId(),
    getGoalId: () => project.project_id,
    onImported: (updated) => opts.onUpdated(updated),
  });
  const folder = buildAddFolderPanel({
    getParentLabel: () => opts.getSelectedNodeLabel(),
    getParentId: () => opts.getSelectedNodeId(),
    getGoalId: () => project.project_id,
    onImported: (updated) => opts.onUpdated(updated),
  });

  const copyRow = document.createElement("div");
  copyRow.className = "map-copy-row";
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "map-copy-button";
  copyBtn.textContent = "Copy as ASCII";
  copyBtn.title = "Copy a classic text tree for docs or chat";
  copyBtn.addEventListener("click", async () => {
    const text = copyAsText(
      project.name,
      middle,
      `#${project.project_id}`,
    );
    try {
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = "Copied";
      window.setTimeout(() => {
        copyBtn.textContent = "Copy as ASCII";
      }, 1200);
    } catch {
      copyBtn.textContent = "Copy failed";
      window.setTimeout(() => {
        copyBtn.textContent = "Copy as ASCII";
      }, 1500);
    }
  });

  const copyGroup = document.createElement("div");
  copyGroup.className = "map-copy-group";
  copyGroup.append(copyBtn, paste.pasteBtn, folder.folderBtn);

  const archiveBtn = document.createElement("button");
  archiveBtn.type = "button";
  archiveBtn.className = "map-copy-button";
  archiveBtn.textContent = `Archive “${displayProjectTitle(project.name)}”`;
  archiveBtn.addEventListener("click", async () => {
    archiveBtn.disabled = true;
    try {
      await archiveProject(project.project_id);
      opts.onArchived();
    } catch (err) {
      archiveBtn.disabled = false;
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      copyRow.appendChild(error);
    }
  });

  copyRow.append(copyGroup, archiveBtn);

  return {
    copyRow,
    pasteForm: paste.pasteForm,
    folderForm: folder.folderForm,
    paste,
    folder,
  };
}
