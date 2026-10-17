// Draws the middle column for one project: the map, its title, and
// which node is selected.
// Clicking empty map space deselects; an empty map shows a hint.

// Contents
//  1. Types
//  2. Helpers
//      - isProgressionTree()
//      - stepIdForLabel()
//      - countUnder()
//  3. Public API
//      - installMapPane()

import { addNode, removeNode, renameProject } from "../../api.js";
import { getActiveUserId, setLastProjectId } from "../../user/activeAccount.js";
import { markHiddenSelection } from "./hiddenSelection.js";
import { displayProjectTitle } from "../create/defaultNames.js";
import { projectChromeHash } from "../create/projectOrder.js";
import { installTitleRename } from "../create/renameProject.js";
import type { ChatPane } from "../chat/chatPane.js";
import {
  dayFocusPlaceholder,
  focusPathPlaceholder,
} from "../chat/focusPath.js";
import { treeWordsElement } from "./drawNodes.js";
import type { NodeMenuActionId } from "./drawNodes.js";
import { installMapScale } from "./zoomAndPan/index.js";
import { mountBottomBar } from "./bottomBar.js";
import { askToConfirm } from "./confirmPopover.js";
import { handleNodeMenuAction } from "./nodeMenu.js";
import type { MapNode, ProjectView } from "../../dataShapes.js";

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
  getSelectedDay: () => string | null;
  /** Select a day of changes (clears the node), or null to let it go. */
  setSelectedDay: (day: string | null) => void;
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

/** A map row's node label — from data-label, not the box text, which
 *  shows the id instead while `/id` is on. */
function beadLabel(row: Element | null | undefined): string | null {
  const bead = row?.querySelector(
    ".progress-bead-btn, .progress-bead-label",
  ) as HTMLElement | null;
  return bead?.dataset.label ?? bead?.textContent ?? null;
}

export function stepIdForLabel(
  host: ParentNode,
  label: string,
): string | null {
  const rows = host.querySelectorAll(".progress-row[data-step-id]");
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const text = beadLabel(row) ?? "";
    if (text === label) {
      return row.getAttribute("data-step-id");
    }
  }
  return null;
}

/** Every node under `stepId`, at any depth; 0 when it has none or is
 *  not in the tree. */
export function countUnder(root: MapNode | null | undefined, stepId: string): number {
  const all = (n: MapNode): number =>
    n.children.reduce((sum, c) => sum + 1 + all(c), 0);
  const find = (n: MapNode): MapNode | null => {
    if (n.id === stepId) return n;
    for (const c of n.children) {
      const hit = find(c);
      if (hit) return hit;
    }
    return null;
  };
  const node = root ? find(root) : null;
  return node ? all(node) : 0;
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
      const label = beadLabel(row) ?? stepId;
      // Picking a node lets a selected day go; redraw so the Status row
      // no longer shows as selected.
      const hadDay = opts.getSelectedDay() !== null;
      opts.setSelectedNode(stepId, label);
      if (hadDay) {
        render();
        return;
      }
      opts.chatInput.placeholder = focusPathPlaceholder(label);
      line.querySelectorAll(".progress-row.is-selected").forEach((el) => {
        el.classList.remove("is-selected");
      });
      row?.classList.add("is-selected");
      markHiddenSelection(line);
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
      return beadLabel(row) ?? stepId;
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
      // Removing takes everything under the node with it and there is
      // no undo yet (TODO Queue 54), so a node with children asks first.
      const under = countUnder(project.node, stepId);
      if (under > 0) {
        const parts = under === 1 ? "the 1 part" : `the ${under} parts`;
        const anchor = line
          .querySelector(`[data-step-id="${CSS.escape(stepId)}"] .progress-menu-toggle`)
          ?.getBoundingClientRect() ?? null;
        const ok = await askToConfirm(
          anchor,
          `Remove “${nodeLabel(stepId)}” and ${parts} under it?`,
          "Remove",
        );
        if (!ok) return;
      }
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
      projectChromeHash(project),
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
      // − / +, ↑, Text | Line change how the map is shown, not what is
      // selected: a hidden selection must survive + so it can surface.
      if (target.closest(".map-top-bar")) return;
      if (target.closest(".progress-add-form")) return;
      if (target.closest(".map-copy-row")) return;
      if (target.closest(".map-paste-form")) return;
      if (target.closest(".map-folder-form")) return;
      // Empty map lets go of a selected node and of a selected day alike.
      const hadDay = opts.getSelectedDay() !== null;
      clearNodeSelection(body);
      if (hadDay) {
        opts.setSelectedDay(null);
        render();
      }
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
      selectedDay: opts.getSelectedDay(),
      onSelectDay: (day) => {
        opts.setSelectedDay(day);
        render();
      },
      resolveStepId: (label) => stepIdForLabel(opts.projectMain, label),
      labelForStepId: (stepId) => beadLabel(
        line.querySelector(`.progress-row[data-step-id="${CSS.escape(stepId)}"]`),
      ),
      onSelectNode: (stepId, label) => {
        markSelected(stepId, `Looking at: ${label}`);
        if (bar.paste.isOpen()) bar.paste.updatePasteHint();
        if (bar.folder.isOpen()) bar.folder.updateFolderHint();
      },
    });
    const heldId = opts.getSelectedNodeId();
    const heldDay = opts.getSelectedDay();
    if (heldId) {
      const label = opts.getSelectedNodeLabel() || nodeLabel(heldId) || heldId;
      markSelected(heldId, `Looking at: ${label}`);
    } else if (heldDay) {
      opts.chatInput.placeholder = dayFocusPlaceholder(heldDay);
    } else {
      opts.chatInput.placeholder = DEFAULT_CHAT_PLACEHOLDER;
    }
  };

  return {
    render,
    clearNodeSelection,
    stepIdForLabel: (label) => stepIdForLabel(opts.projectMain, label),
  };
}
