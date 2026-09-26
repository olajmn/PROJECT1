// Draws the middle column for one project: the map, its title, and
// which node is selected.
// Clicking empty map space deselects; an empty map shows a hint.

// Contents
//  1. Types
//  2. Helpers
//      - isProgressionTree()
//      - stepIdForLabel()
//  3. Public API
//      - installMapPane()

import { addNode, removeNode, renameProject } from "../../api.js";
import { getActiveUserId, setLastProjectId } from "../../user/activeId.js";
import { displayProjectTitle } from "../create/defaultNames.js";
import { installTitleRename } from "../create/renameProject.js";
import type { ChatPane } from "../chat/chatPane.js";
import {
  focusPathPlaceholder,
} from "../chat/focusPath.js";
import { treeWordsElement } from "./drawNodes.js";
import type { NodeMenuActionId } from "./drawNodes.js";
import { installMapScale } from "./zoomAndPan/index.js";
import { mountBottomBar } from "./bottomBar.js";
import { handleNodeMenuAction } from "./nodeMenu.js";
import type { ProjectView } from "../../dataShapes.js";

// 1. Types

const PROGRESSION_STEP_ID = /^p\d+$/;
const DEFAULT_CHAT_PLACEHOLDER = "Talk about this project…";

export type MapPane = {
  render: () => void;
  clearNodeSelection: (scope?: ParentNode) => void;
  stepIdForLabel: (label: string) => string | null;
};

type MapPaneOpts = {
  projectMain: HTMLElement;
  mainEmpty: HTMLParagraphElement;
  projectChat: HTMLElement;
  chatInput: HTMLTextAreaElement;
  chatError: HTMLParagraphElement;
  chatPane: ChatPane;
  getProject: () => ProjectView | null;
  isCreateOpen: () => boolean;
  mountCreate: () => void;
  getSelectedNodeId: () => string | null;
  getSelectedNodeLabel: () => string | null;
  setSelectedNode: (stepId: string | null, label: string | null) => void;
  onCloseProject: () => void;
  onUpdated: (updated: ProjectView) => void;
  onArchived: (projectId: number) => void;
  onBrandRender: () => void;
};

// 2. Helpers

export function isProgressionTree(
  node: { children: { id: string }[] },
): boolean {
  return node.children.some((child) => PROGRESSION_STEP_ID.test(child.id));
}

export function stepIdForLabel(
  host: ParentNode,
  label: string,
): string | null {
  const rows = host.querySelectorAll(".progress-row[data-step-id]");
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const text =
      row.querySelector(".progress-bead-btn, .progress-bead-label")
        ?.textContent ?? "";
    if (text === label) {
      return row.getAttribute("data-step-id");
    }
  }
  return null;
}

// 3. Public API

export function installMapPane(opts: MapPaneOpts): MapPane {
  const clearNodeSelection = (scope: ParentNode = opts.projectMain): void => {
    opts.setSelectedNode(null, null);
    opts.chatInput.placeholder = DEFAULT_CHAT_PLACEHOLDER;
    scope.querySelectorAll(".progress-row.is-selected").forEach((el) => {
      el.classList.remove("is-selected");
    });
    scope.querySelectorAll(".node-focus-note").forEach((el) => el.remove());
  };

  const render = (): void => {
    const project = opts.getProject();
    const activeUserId = getActiveUserId();
    if (activeUserId !== null && project) {
      setLastProjectId(activeUserId, project.project_id);
    }
    opts.projectMain.innerHTML = "";
    opts.chatError.hidden = true;
    opts.onBrandRender();

    if (!project || opts.isCreateOpen()) {
      opts.mainEmpty.hidden = true;
      opts.mountCreate();
      opts.projectChat.hidden = false;
      opts.chatPane.fillEmpty("Select a project to open its chat.");
      return;
    }

    opts.mainEmpty.hidden = true;
    opts.projectChat.hidden = false;

    const body = document.createElement("div");
    body.className = "project-body";

    const middle = project.node?.children ?? [];
    const canSelect = project.node ? isProgressionTree(project.node) : false;
    let line: HTMLDivElement;

    const markSelected = (stepId: string, note: string) => {
      const row = line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
      const label =
        row?.querySelector(".progress-bead-btn, .progress-bead-label")
          ?.textContent ?? stepId;
      opts.setSelectedNode(stepId, label);
      opts.chatInput.placeholder = focusPathPlaceholder(label);
      line.querySelectorAll(".progress-row.is-selected").forEach((el) => {
        el.classList.remove("is-selected");
      });
      row?.classList.add("is-selected");
      let focus = body.querySelector(
        ".node-focus-note",
      ) as HTMLParagraphElement | null;
      if (!focus) {
        focus = document.createElement("p");
        focus.className = "node-focus-note";
        const scaleHost =
          (line.closest(".map-scale-viewport") as HTMLElement | null) ?? line;
        scaleHost.insertAdjacentElement("afterend", focus);
      }
      focus.textContent = note;
    };

    const nodeLabel = (stepId: string): string => {
      const row = line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
      return (
        row?.querySelector(".progress-bead-btn, .progress-bead-label")
          ?.textContent ?? stepId
      );
    };

    const addBead = async (trimmed: string, parentId?: string) => {
      line.classList.add("plan-busy");
      try {
        const updated = await addNode(
          project.project_id,
          trimmed,
          parentId,
        );
        opts.onUpdated(updated);
      } catch (err) {
        line.classList.remove("plan-busy");
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        line.appendChild(error);
      }
    };

    const removeBead = async (stepId: string) => {
      line.classList.add("plan-busy");
      try {
        const updated = await removeNode(project.project_id, stepId);
        if (stepId === opts.getSelectedNodeId()) {
          opts.setSelectedNode(null, null);
          opts.chatInput.placeholder = DEFAULT_CHAT_PLACEHOLDER;
        }
        opts.onUpdated(updated);
      } catch (err) {
        line.classList.remove("plan-busy");
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        line.appendChild(error);
      }
    };

    const bar = mountBottomBar({
      project,
      middle,
      getSelectedNodeId: opts.getSelectedNodeId,
      getSelectedNodeLabel: opts.getSelectedNodeLabel,
      onUpdated: opts.onUpdated,
      onArchived: () => opts.onArchived(project.project_id),
    });

    const onMenuAction = async (
      action: NodeMenuActionId,
      stepId: string,
    ) => {
      await handleNodeMenuAction(action, stepId, {
        project,
        line,
        projectMain: opts.projectMain,
        chatInput: opts.chatInput,
        markSelected,
        nodeLabel,
        removeBead,
        openPaste: () => bar.paste.open(),
        onUpdated: opts.onUpdated,
      });
    };

    const renameTitle = async (name: string): Promise<void> => {
      try {
        opts.onUpdated(await renameProject(project.project_id, name));
      } catch (err) {
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        body.appendChild(error);
        throw err;
      }
    };

    line = treeWordsElement(
      displayProjectTitle(project.name),
      middle,
      canSelect
        ? (stepId: string) => {
            markSelected(stepId, `Looking at: ${nodeLabel(stepId)}`);
            if (bar.paste.isOpen()) bar.paste.updatePasteHint();
            if (bar.folder.isOpen()) bar.folder.updateFolderHint();
          }
        : undefined,
      addBead,
      removeBead,
      opts.getSelectedNodeId(),
      canSelect ? onMenuAction : undefined,
      `#${project.project_id}`,
    );
    const nameText = line.querySelector(".progress-name-label");
    if (nameText instanceof HTMLElement) {
      installTitleRename(nameText, project.name, renameTitle);
    }
    body.appendChild(line);
    installMapScale(body, line, project.project_id, {
      onClose: () => opts.onCloseProject(),
    });

    body.appendChild(bar.copyRow);
    body.appendChild(bar.pasteForm);
    body.appendChild(bar.folderForm);

    body.addEventListener("click", (event) => {
      if (bar.paste.isOpen() || bar.folder.isOpen()) return;
      const target = event.target as Element | null;
      if (!target) return;
      if (target.closest(".progress-row")) return;
      if (target.closest(".progress-add-form")) return;
      if (target.closest(".map-copy-row")) return;
      if (target.closest(".map-paste-form")) return;
      if (target.closest(".map-folder-form")) return;
      clearNodeSelection(body);
    });

    if (!project.node) {
      const hint = document.createElement("p");
      hint.className = "project-hint";
      hint.textContent =
        "Add steps with +, or talk — the map starts empty.";
      body.insertBefore(hint, bar.copyRow);
    }

    opts.projectMain.appendChild(body);

    opts.chatPane.fillProject({
      project,
      resolveStepId: (label) => stepIdForLabel(opts.projectMain, label),
      onSelectNode: (stepId, label) => {
        markSelected(stepId, `Looking at: ${label}`);
        if (bar.paste.isOpen()) bar.paste.updatePasteHint();
        if (bar.folder.isOpen()) bar.folder.updateFolderHint();
      },
    });
    const heldId = opts.getSelectedNodeId();
    if (heldId) {
      const label = opts.getSelectedNodeLabel() || nodeLabel(heldId) || heldId;
      markSelected(heldId, `Looking at: ${label}`);
    }
  };

  return {
    render,
    clearNodeSelection,
    stepIdForLabel: (label) => stepIdForLabel(opts.projectMain, label),
  };
}
