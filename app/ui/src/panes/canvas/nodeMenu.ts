// What the ⋯ menu on a node does: Add here, Remove, Talk about this,
// Paste structure, Suggest.

// Contents
//  1. Types
//  2. Public API
//      - handleNodeMenuAction()
//      - childCountUnder()

import { suggestChildren } from "../../api.js";
import type { MapNode, ProjectView } from "../../dataShapes.js";
import type { NodeMenuActionId } from "./drawNodes.js";

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

/** How many direct children a node has in this tree. */
export function childCountUnder(
  root: MapNode | null | undefined,
  stepId: string,
): number {
  const walk = (
    n: { id: string; children: typeof n[] } | null | undefined,
  ): number | null => {
    if (!n) return null;
    if (n.id === stepId) return n.children.length;
    for (const c of n.children) {
      const hit = walk(c);
      if (hit !== null) return hit;
    }
    return null;
  };
  return walk(root) ?? 0;
}

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
  // suggest — agent proposes children (old zoom, on request only)
  ctx.markSelected(stepId, `Suggesting under: ${label}…`);
  ctx.line.classList.add("plan-busy");
  try {
    const beforeCount = childCountUnder(ctx.project.node, stepId);
    const updated = await suggestChildren(ctx.project.project_id, stepId);
    const afterCount = childCountUnder(updated.node, stepId);
    ctx.onUpdated(updated);
    if (afterCount <= beforeCount) {
      const note = document.createElement("p");
      note.className = "node-focus-note";
      note.textContent =
        "Nothing more to suggest under that node — already fine enough.";
      ctx.projectMain
        .querySelector(".map-scale-viewport, .progress-line")
        ?.insertAdjacentElement("afterend", note);
    }
  } catch (err) {
    ctx.line.classList.remove("plan-busy");
    const error = document.createElement("p");
    error.className = "error";
    error.textContent = `(error: ${(err as Error).message})`;
    ctx.line.appendChild(error);
  }
}
