// What the ⋯ menu on a node does: Add here, Remove, Move up/down,
// Rename, Talk about this, Paste structure, Save as tree, Insert saved tree.

// Contents
//  1. Types
//  2. Public API
//      - handleNodeMenuAction()

import type { ProjectView } from "../../dataShapes.js";
import type { NodeMenuActionId } from "./drawNodes.js";
import { moveNode } from "../../api.js";
import { saveTreeFromNode } from "./savedTrees/saveTree.js";
import { openInsertTreePicker } from "./savedTrees/insertTree.js";
import { startNodeRename } from "./renameNode.js";

// 1. Types

export type NodeMenuContext = {
  project: ProjectView;
  line: HTMLElement;
  projectMain: HTMLElement;
  chatInput: HTMLTextAreaElement;
  markSelected: (stepId: string, note: string) => void;
  nodeLabel: (stepId: string) => string;
  removeBead: (stepId: string) => Promise<void>;
  openPaste: () => void;
  onUpdated: (updated: ProjectView) => void;
};

// 2. Public API

export async function handleNodeMenuAction(
  action: NodeMenuActionId,
  stepId: string,
  ctx: NodeMenuContext,
): Promise<void> {
  const label = ctx.nodeLabel(stepId);
  if (action === "register") {
    ctx.markSelected(stepId, `Add under: ${label}`);
    const row = ctx.line.querySelector(
      `[data-step-id="${CSS.escape(stepId)}"]`,
    );
    const form = row?.querySelector(
      ".progress-add-form",
    ) as HTMLFormElement | null;
    if (form) {
      form.hidden = false;
      const input = form.querySelector(
        ".progress-add-input",
      ) as HTMLInputElement | null;
      input?.focus();
    }
    return;
  }
  if (action === "remove") {
    await ctx.removeBead(stepId);
    return;
  }
  if (action === "move_up" || action === "move_down") {
    const direction = action === "move_up" ? "up" : "down";
    try {
      ctx.onUpdated(await moveNode(ctx.project.project_id, stepId, direction));
    } catch (err) {
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = `(error: ${(err as Error).message})`;
      ctx.line.appendChild(error);
    }
    return;
  }
  if (action === "rename") {
    startNodeRename(stepId, ctx);
    return;
  }
  if (action === "analyze") {
    ctx.markSelected(stepId, `Talk about: ${label}`);
    ctx.chatInput.focus();
    return;
  }
  if (action === "paste") {
    ctx.markSelected(stepId, `Will import under: ${label}`);
    ctx.openPaste();
    return;
  }
  if (action === "save_tree") {
    await saveTreeFromNode(stepId, label, ctx);
    return;
  }
  if (action === "insert_tree") {
    ctx.markSelected(stepId, `Insert a saved tree under: ${label}`);
    await openInsertTreePicker(stepId, ctx);
  }
}
