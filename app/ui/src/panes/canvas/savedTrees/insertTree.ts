// ⋯ menu "Insert saved tree…": pick one of the account's saved trees
// and insert it under the node as new nodes (fresh ids; a clashing top
// label is numbered by the server). × on a row deletes it from the
// library only — nothing already inserted changes.

// Contents
//  1. Public API
//      - openInsertTreePicker()
//  2. Picker
//      - buildRow()
//      - placeNear() / closePicker()

import {
  deleteSavedTree,
  fetchSavedTrees,
  insertSavedTree,
} from "../../../api.js";
import type { SavedTreeView } from "../../../dataShapes.js";
import type { NodeMenuContext } from "../nodeMenu.js";

// 1. Public API

export async function openInsertTreePicker(
  stepId: string,
  ctx: NodeMenuContext,
): Promise<void> {
  closePicker();
  let trees: SavedTreeView[];
  try {
    trees = await fetchSavedTrees(ctx.project.project_id);
  } catch (err) {
    ctx.markSelected(stepId, `Could not load saved trees: ${(err as Error).message}`);
    return;
  }

  const picker = document.createElement("div");
  picker.className = "progress-menu saved-tree-picker";
  picker.setAttribute("role", "menu");

  const insert = async (tree: SavedTreeView) => {
    closePicker();
    ctx.line.classList.add("plan-busy");
    try {
      ctx.onUpdated(
        await insertSavedTree(ctx.project.project_id, tree.id, stepId),
      );
    } catch (err) {
      ctx.line.classList.remove("plan-busy");
      ctx.markSelected(stepId, `Could not insert "${tree.name}": ${(err as Error).message}`);
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

  const row = ctx.line.querySelector(`[data-step-id="${CSS.escape(stepId)}"]`);
  const anchor =
    (row?.querySelector(".progress-menu-toggle") as HTMLElement | null) ??
    (row as HTMLElement | null);
  document.body.appendChild(picker);
  placeNear(picker, anchor);
  openPicker = picker;
  document.addEventListener("click", onOutside, true);
  document.addEventListener("keydown", onKey);
  document.addEventListener("wheel", closePicker, { passive: true });
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

/** Fixed on <body> under the ⋯ toggle, as the node menu is — the map
 *  stage is transformed, so fixed positioning inside it would drift. */
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

function onOutside(event: MouseEvent): void {
  if (openPicker && !openPicker.contains(event.target as Node)) closePicker();
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") closePicker();
}

function closePicker(): void {
  if (!openPicker) return;
  openPicker.remove();
  openPicker = null;
  document.removeEventListener("click", onOutside, true);
  document.removeEventListener("keydown", onKey);
  document.removeEventListener("wheel", closePicker);
  window.removeEventListener("resize", closePicker);
}
