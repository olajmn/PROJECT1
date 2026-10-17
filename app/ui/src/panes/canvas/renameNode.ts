// ⋯ Rename: the node's name becomes a text field in place; Enter or
// leaving the field saves, Escape cancels. The node keeps its id, so its
// chat turns stay attached (docs/05-decisions.md #52, #71). Same editing
// idiom as the project title (panes/create/renameProject.ts).

import type { ProjectView } from "../../dataShapes.js";
import { renameNode } from "../../api.js";

export type RenameNodeContext = {
  project: ProjectView;
  line: HTMLElement;
  onUpdated: (updated: ProjectView) => void;
};

export function startNodeRename(stepId: string, ctx: RenameNodeContext): void {
  const row = ctx.line.querySelector(
    `.progress-row[data-step-id="${CSS.escape(stepId)}"]`,
  );
  const nameEl = row?.querySelector(
    ".progress-bead-btn, .progress-bead-label",
  ) as HTMLElement | null;
  if (!nameEl || row?.querySelector(".progress-node-rename")) return;
  const current = nameEl.dataset.label ?? nameEl.textContent ?? "";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "progress-node-rename";
  input.value = current;
  input.setAttribute("aria-label", "Node name");
  nameEl.replaceWith(input);
  input.focus();
  input.select();

  let closed = false;
  const restore = (): void => {
    if (input.parentElement) input.replaceWith(nameEl);
  };
  const finish = async (save: boolean): Promise<void> => {
    if (closed) return;
    closed = true;
    const next = input.value.trim();
    if (!save || !next || next === current.trim()) {
      restore();
      return;
    }
    try {
      ctx.onUpdated(await renameNode(ctx.project.project_id, stepId, next));
    } catch (err) {
      restore();
      // e.g. a sibling already has that name; shown under the node.
      const error = document.createElement("p");
      error.className = "error";
      error.textContent = (err as Error).message;
      row?.appendChild(error);
      window.setTimeout(() => error.remove(), 4000);
    }
  };

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      void finish(true);
    } else if (event.key === "Escape") {
      event.preventDefault();
      void finish(false);
    }
  });
  input.addEventListener("blur", () => void finish(true));
  // Typing or clicking in the field must not pan the map or select nodes.
  input.addEventListener("pointerdown", (event) => event.stopPropagation());
  input.addEventListener("click", (event) => event.stopPropagation());
}
