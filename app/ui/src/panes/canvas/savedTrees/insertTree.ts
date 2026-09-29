// The saved-tree picker: lists the account's saved trees and inserts
// one as new nodes (fresh ids; a clashing top label is numbered by the
// server). Opened from a node's ⋯ "Insert saved tree…" (under that node)
// or the bar's + Add → "Insert saved tree…" (under the selected node, or
// at the top level). × on a row deletes it from the library only — nothing
// already inserted changes.

// Contents
//  1. Public API
//      - openInsertTreePicker()
//      - openSavedTreesPicker()
//  2. Picker
//      - buildRow()
//      - closePicker()

import {
  deleteSavedTree,
  fetchSavedTrees,
  insertSavedTree,
} from "../../../api.js";
import type { ProjectView, SavedTreeView } from "../../../dataShapes.js";
import type { NodeMenuContext } from "../nodeMenu.js";
import { askToConfirm } from "../confirmPopover.js";
import { placePopover } from "../placePopover.js";

// 1. Public API

export type PickerTarget = {
  projectId: number;
  /** null inserts at the top level of the map. */
  parentId: string | null;
  parentLabel: string | null;
  anchor: HTMLElement | null;
  onUpdated: (updated: ProjectView) => void;
  onError: (message: string) => void;
};

/** From a node's ⋯ menu: insert under that node. */
export async function openInsertTreePicker(
  stepId: string,
  ctx: NodeMenuContext,
): Promise<void> {
  const row = ctx.line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
  await openSavedTreesPicker({
    projectId: ctx.project.project_id,
    parentId: stepId,
    parentLabel: ctx.nodeLabel(stepId),
    anchor:
      (row?.querySelector(".progress-menu-toggle") as HTMLElement | null) ??
      (row as HTMLElement | null),
    onUpdated: (updated) => ctx.onUpdated(updated),
    onError: (message) => ctx.markSelected(stepId, message),
  });
}

/** Open the picker for `target`, closing one already open. */
export async function openSavedTreesPicker(target: PickerTarget): Promise<void> {
  closePicker();
  let trees: SavedTreeView[];
  try {
    trees = await fetchSavedTrees(target.projectId);
  } catch (err) {
    target.onError(`Could not load saved trees: ${(err as Error).message}`);
    return;
  }

  const picker = document.createElement("div");
  picker.className = "progress-menu saved-tree-picker";
  picker.setAttribute("role", "menu");

  const where = document.createElement("p");
  where.className = "saved-tree-target";
  where.textContent = target.parentId
    ? `Insert under: ${target.parentLabel ?? target.parentId}`
    : "Insert at the top level";
  picker.appendChild(where);

  const insert = async (tree: SavedTreeView) => {
    closePicker();
    try {
      target.onUpdated(
        await insertSavedTree(target.projectId, tree.id, target.parentId),
      );
    } catch (err) {
      target.onError(`Could not insert "${tree.name}": ${(err as Error).message}`);
    }
  };

  const showEmpty = () => {
    const empty = document.createElement("p");
    empty.className = "saved-tree-empty";
    empty.textContent = "No saved trees yet. Use Save as tree on a node.";
    picker.appendChild(empty);
  };

  if (trees.length === 0) showEmpty();
  for (const tree of trees) {
    picker.appendChild(
      buildRow(tree, insert, (row) => {
        row.remove();
        if (!picker.querySelector(".saved-tree-row")) showEmpty();
      }),
    );
  }

  document.body.appendChild(picker);
  placePopover(picker, target.anchor?.getBoundingClientRect() ?? null);
  openPicker = picker;
  document.addEventListener("click", onOutside, true);
  document.addEventListener("keydown", onKey);
  document.addEventListener("wheel", onWheel, { passive: true });
  window.addEventListener("resize", closePicker);
}

// 2. Picker

let openPicker: HTMLElement | null = null;

function buildRow(
  tree: SavedTreeView,
  onInsert: (tree: SavedTreeView) => void,
  onDeleted: (row: HTMLElement) => void,
): HTMLElement {
  const row = document.createElement("div");
  row.className = "saved-tree-row";

  const pick = document.createElement("button");
  pick.type = "button";
  pick.className = "progress-menu-item saved-tree-pick";
  pick.textContent = tree.name;
  const count = document.createElement("span");
  count.className = "saved-tree-count";
  count.textContent = String(tree.node_count);
  pick.appendChild(count);
  pick.addEventListener("click", () => onInsert(tree));

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "saved-tree-delete";
  remove.textContent = "×";
  // The browser's own label: the picker scrolls, so a CSS label (tip.ts)
  // would be clipped inside it.
  remove.title = "Delete from saved trees";
  remove.addEventListener("click", async () => {
    const ok = await askToConfirm(
      remove.getBoundingClientRect(),
      `Delete saved tree “${tree.name}”?`,
      "Delete",
    );
    if (!ok) return;
    try {
      await deleteSavedTree(tree.id);
      onDeleted(row);
    } catch (err) {
      remove.title = (err as Error).message;
    }
  });

  row.append(pick, remove);
  return row;
}

/** A click outside the picker closes it. */
function onOutside(event: MouseEvent): void {
  const target = event.target as Node;
  if (!openPicker || openPicker.contains(target)) return;
  closePicker();
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") closePicker();
}

/** Scrolling the list itself must not close it. */
function onWheel(event: WheelEvent): void {
  if (openPicker && !openPicker.contains(event.target as Node)) closePicker();
}

function closePicker(): void {
  if (!openPicker) return;
  openPicker.remove();
  openPicker = null;
  document.removeEventListener("click", onOutside, true);
  document.removeEventListener("keydown", onKey);
  document.removeEventListener("wheel", onWheel);
  window.removeEventListener("resize", closePicker);
}
