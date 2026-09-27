// The saved-tree picker: lists the account's saved trees and inserts
// one as new nodes (fresh ids; a clashing top label is numbered by the
// server). Opened from a node's ⋯ "Insert saved tree…" (under that node)
// or the bottom bar's "Saved trees" (under the selected node, or at the
// top level). × on a row deletes it from the library only — nothing
// already inserted changes.

// Contents
//  1. Public API
//      - openInsertTreePicker()
//      - openSavedTreesPicker()
//  2. Picker
//      - buildRow()
//      - placeNear() / closePicker()

import {
  deleteSavedTree,
  fetchSavedTrees,
  insertSavedTree,
} from "../../../api.js";
import type { ProjectView, SavedTreeView } from "../../../dataShapes.js";
import type { NodeMenuContext } from "../nodeMenu.js";

// 1. Public API

export type PickerTarget = {
  projectId: number;
  /** null inserts at the top level of the map. */
  parentId: string | null;
  parentLabel: string | null;
  anchor: HTMLElement | null;
  /** The anchor toggles the picker (bottom-bar button): a click on it
   *  is left to its own handler instead of closing as "outside". */
  anchorToggles?: boolean;
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

/** Open the picker for `target`. With `anchorToggles`, a second call
 *  from the same anchor while it is open closes it instead. */
export async function openSavedTreesPicker(target: PickerTarget): Promise<void> {
  if (openPicker && target.anchorToggles && openAnchor === target.anchor) {
    closePicker();
    return;
  }
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
  placeNear(picker, target.anchor);
  openPicker = picker;
  openAnchor = target.anchorToggles ? target.anchor : null;
  document.addEventListener("click", onOutside, true);
  document.addEventListener("keydown", onKey);
  document.addEventListener("wheel", onWheel, { passive: true });
  window.addEventListener("resize", closePicker);
}

// 2. Picker

let openPicker: HTMLElement | null = null;
let openAnchor: HTMLElement | null = null;

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
  remove.title = "Delete from saved trees";
  remove.addEventListener("click", async () => {
    if (!window.confirm(`Delete saved tree "${tree.name}"?`)) return;
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

/** Fixed on <body> next to the anchor, as the node menu is — the map
 *  stage is transformed, so fixed positioning inside it would drift.
 *  Flips above the anchor when there is no room below (bottom bar). */
function placeNear(picker: HTMLElement, anchor: HTMLElement | null): void {
  const rect = anchor?.getBoundingClientRect();
  picker.style.left = `${Math.round(rect?.left ?? 16)}px`;
  picker.style.top = `${Math.round((rect?.bottom ?? 16) + 4)}px`;
  requestAnimationFrame(() => {
    const box = picker.getBoundingClientRect();
    if (rect && box.bottom > window.innerHeight - 8) {
      picker.style.top = `${Math.max(8, Math.round(rect.top - box.height - 4))}px`;
    }
    if (box.right > window.innerWidth - 8) {
      picker.style.left = `${Math.max(8, Math.round(window.innerWidth - box.width - 8))}px`;
    }
  });
}

/** Outside click closes; a click on the anchor is left to its own
 *  handler, which toggles. */
function onOutside(event: MouseEvent): void {
  const target = event.target as Node;
  if (!openPicker || openPicker.contains(target)) return;
  if (openAnchor?.contains(target)) return;
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
  openAnchor = null;
  document.removeEventListener("click", onOutside, true);
  document.removeEventListener("keydown", onKey);
  document.removeEventListener("wheel", onWheel);
  window.removeEventListener("resize", closePicker);
}
