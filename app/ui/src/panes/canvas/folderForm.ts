/**
 * Add folder: a path field that turns one real folder into map nodes.
 */

import { chooseFolder, addFolder } from "../../api.js";
import type { ProjectView } from "../../dataShapes.js";

export type AddFolderPanel = {
  folderBtn: HTMLButtonElement;
  folderForm: HTMLFormElement;
  updateFolderHint: () => void;
  isOpen: () => boolean;
};

export function buildAddFolderPanel(opts: {
  getParentLabel: () => string | null;
  getParentId: () => string | null;
  getProjectId: () => number;
  onImported: (updated: ProjectView) => void;
}): AddFolderPanel {
  const folderBtn = document.createElement("button");
  folderBtn.type = "button";
  folderBtn.className = "map-copy-button";
  folderBtn.textContent = "Add folder";
  folderBtn.title = "Turn a folder on this computer into map nodes";

  const folderForm = document.createElement("form");
  folderForm.className = "map-folder-form";
  folderForm.hidden = true;

  const folderInput = document.createElement("input");
  folderInput.type = "text";
  folderInput.className = "map-folder-input";
  folderInput.placeholder = "/path/to/folder";
  folderInput.spellcheck = false;

  const folderHint = document.createElement("p");
  folderHint.className = "map-paste-hint";
  const updateFolderHint = () => {
    const label = opts.getParentLabel();
    folderHint.textContent = label
      ? `Will add under: ${label}`
      : "Will add at the project root.";
  };
  updateFolderHint();

  const folderActions = document.createElement("div");
  folderActions.className = "map-paste-actions";
  const folderChoose = document.createElement("button");
  folderChoose.type = "button";
  folderChoose.textContent = "Choose";
  folderChoose.title = "Pick a folder. The path is filled in for you.";
  const folderSubmit = document.createElement("button");
  folderSubmit.type = "submit";
  folderSubmit.textContent = "Add";
  const folderCancel = document.createElement("button");
  folderCancel.type = "button";
  folderCancel.textContent = "Cancel";
  const folderError = document.createElement("p");
  folderError.className = "error";
  folderError.hidden = true;
  folderActions.append(folderChoose, folderSubmit, folderCancel);
  folderForm.append(folderInput, folderHint, folderActions, folderError);

  folderChoose.addEventListener("click", async () => {
    folderError.hidden = true;
    folderChoose.disabled = true;
    try {
      const path = await chooseFolder();
      if (path) folderInput.value = path;
    } catch (err) {
      folderError.hidden = false;
      folderError.textContent = `(error: ${(err as Error).message})`;
    } finally {
      folderChoose.disabled = false;
    }
  });
  folderBtn.addEventListener("click", () => {
    folderForm.hidden = !folderForm.hidden;
    if (!folderForm.hidden) {
      updateFolderHint();
      folderInput.focus();
    }
  });
  folderCancel.addEventListener("click", () => {
    folderForm.hidden = true;
    folderInput.value = "";
    folderError.hidden = true;
  });
  folderForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const folder = folderInput.value.trim();
    if (!folder) return;
    folderError.hidden = true;
    folderSubmit.disabled = true;
    try {
      const updated = await addFolder(
        opts.getProjectId(),
        folder,
        opts.getParentId(),
      );
      folderInput.value = "";
      folderForm.hidden = true;
      opts.onImported(updated);
    } catch (err) {
      folderError.hidden = false;
      folderError.textContent = `(error: ${(err as Error).message})`;
    } finally {
      folderSubmit.disabled = false;
    }
  });

  return {
    folderBtn,
    folderForm,
    updateFolderHint,
    isOpen: () => !folderForm.hidden,
  };
}
