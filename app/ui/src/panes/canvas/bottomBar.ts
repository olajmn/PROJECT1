// The bar under the map: "+ Add" (Paste structure, Add folder, Saved
// trees, in one menu — addMenu.ts) on the left; Copy as ASCII and
// Archive as icon buttons on the right.

// Contents
//  1. Types
//  2. Public API
//      - mountBottomBar()
//  3. Icons
//      - iconButton() / setIcon()

import { archiveProject } from "../../api.js";
import { displayProjectTitle } from "../create/defaultNames.js";
import { projectChromeHash } from "../create/projectOrder.js";
import { setTip } from "../../shell/tip.js";
import { buildAddMenu } from "./addMenu.js";
import { copyAsText } from "./copyAsText.js";
import { buildAddFolderPanel } from "./folderForm.js";
import { buildPasteTreePanel } from "./pasteForm.js";
import { openSavedTreesPicker } from "./savedTrees/insertTree.js";
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
    getProjectId: () => project.project_id,
    onImported: (updated) => opts.onUpdated(updated),
  });
  const folder = buildAddFolderPanel({
    getParentLabel: () => opts.getSelectedNodeLabel(),
    getParentId: () => opts.getSelectedNodeId(),
    getProjectId: () => project.project_id,
    onImported: (updated) => opts.onUpdated(updated),
  });

  const copyRow = document.createElement("div");
  copyRow.className = "map-copy-row";
  const copyTip = "Copy as ASCII";
  const copyBtn = iconButton("copy", copyTip);
  copyBtn.addEventListener("click", async () => {
    const text = copyAsText(
      project.name,
      middle,
      projectChromeHash(project),
    );
    // Brief feedback in the icon itself (a check), then back to copy.
    try {
      await navigator.clipboard.writeText(text);
      setIcon(copyBtn, "check");
      setTip(copyBtn, "Copied", "above", "end");
    } catch {
      setTip(copyBtn, "Copy failed", "above", "end");
    }
    window.setTimeout(() => {
      setIcon(copyBtn, "copy");
      setTip(copyBtn, copyTip, "above", "end");
    }, 1200);
  });

  const showError = (message: string): void => {
    const error = document.createElement("p");
    error.className = "error";
    error.textContent = `(error: ${message})`;
    copyRow.appendChild(error);
  };

  // The paste / folder panels keep their own (now unplaced) toggle
  // buttons; the menu only opens them. Saved trees is the same picker
  // as a node's ⋯ "Insert saved tree…", anchored to the Add button: it
  // inserts under the selected node, or at the top level.
  const addBtn = buildAddMenu([
    {
      label: "Paste structure",
      detail: "Import a pasted outline or ASCII tree",
      run: () => paste.open(),
    },
    {
      label: "Add folder",
      detail: "Turn a folder on this computer into map nodes",
      run: () => {
        if (!folder.isOpen()) folder.folderBtn.click();
      },
    },
    {
      label: "Insert saved tree…",
      detail: "Insert one of your saved trees",
      run: (anchor) => {
        void openSavedTreesPicker({
          projectId: project.project_id,
          parentId: opts.getSelectedNodeId(),
          parentLabel: opts.getSelectedNodeLabel(),
          anchor,
          anchorToggles: false,
          onUpdated: (updated) => opts.onUpdated(updated),
          onError: showError,
        });
      },
    },
  ]);

  const copyGroup = document.createElement("div");
  copyGroup.className = "map-copy-group";
  copyGroup.append(addBtn);

  const archiveBtn = iconButton(
    "archive",
    `Archive “${displayProjectTitle(project.name)}”`,
  );
  archiveBtn.addEventListener("click", async () => {
    archiveBtn.disabled = true;
    try {
      await archiveProject(project.project_id);
      opts.onArchived();
    } catch (err) {
      archiveBtn.disabled = false;
      showError((err as Error).message);
    }
  });

  const iconGroup = document.createElement("div");
  iconGroup.className = "map-copy-group";
  iconGroup.append(copyBtn, archiveBtn);

  copyRow.append(copyGroup, iconGroup);

  return {
    copyRow,
    pasteForm: paste.pasteForm,
    folderForm: folder.folderForm,
    paste,
    folder,
  };
}

// 3. Icons

// 24×24 stroke icons, drawn in the text colour (currentColor).
const ICONS = {
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  archive: '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/>',
} as const;

type IconName = keyof typeof ICONS;

/** A square button showing only an icon; `tip` is its hover label and
 *  accessible name. Both sit at the bar's right edge, so the label is
 *  end-aligned to stay inside the window. */
function iconButton(icon: IconName, tip: string): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "map-copy-button map-icon-button";
  setTip(button, tip, "above", "end");
  setIcon(button, icon);
  return button;
}

function setIcon(button: HTMLButtonElement, icon: IconName): void {
  button.innerHTML =
    `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
    `stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">` +
    `${ICONS[icon]}</svg>`;
}
