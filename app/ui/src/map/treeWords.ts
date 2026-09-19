/**
 * Write the words on the live project map (DOM rows + controls).
 * Who-under-who from mapFamily; lines from mapLines.
 */

import type { PlanningNode } from "../types.js";
import { installMapLines } from "./mapLines.js";
import {
  applyFamilyAttrs,
  familyById,
  layoutFamily,
  type MapFamilyNode,
} from "./mapFamily.js";

export type PlanClickHandler = (stepId: string) => void;
/** parentId omitted/undefined = add at project root. */
export type AddStepHandler = (label: string, parentId?: string) => void;
export type RemoveStepHandler = (stepId: string) => void;
export type NodeMenuActionId = "register" | "suggest" | "analyze" | "paste";
export type NodeMenuHandler = (action: NodeMenuActionId, stepId: string) => void;

const NODE_MENU_ACTIONS: {
  id: NodeMenuActionId;
  label: string;
  detail: string;
}[] = [
  {
    id: "register",
    label: "Add here",
    detail: "You name a child under this node — no AI, just record it.",
  },
  {
    id: "suggest",
    label: "Suggest structure",
    detail: "Ask the agent to propose children under this node.",
  },
  {
    id: "analyze",
    label: "Talk about this",
    detail: "Focus chat on this node so you can ask what it means.",
  },
  {
    id: "paste",
    label: "Paste structure",
    detail: "Import a pasted outline or ASCII tree as children here.",
  },
];

const PROGRESSION_LIKE = /^p\d+$/;

function childGuide(_parentContinues: boolean): string {
  // Indent width only; SVG draws connectors. Kept for stem length → depth.
  return "    ";
}

function indentWidth(depth: number): string {
  // Each depth steps right — "dimensions" like the classic ASCII map.
  return `${0.55 + depth * 1.15}rem`;
}

/** Inline + form that calls onAddStep(label, parentId). */
function attachAddControl(
  row: HTMLElement,
  onAddStep: AddStepHandler,
  parentId?: string,
): void {
  const add = document.createElement("button");
  add.type = "button";
  add.className = "progress-add progress-add-inline";
  add.textContent = "+";
  add.title = parentId
    ? "Add a node under this one"
    : "Add a node under the project";

  const form = document.createElement("form");
  form.className = "progress-add-form";
  form.hidden = true;
  const input = document.createElement("input");
  input.type = "text";
  input.className = "progress-add-input";
  input.placeholder = "Node name…";
  input.autocomplete = "off";
  const save = document.createElement("button");
  save.type = "submit";
  save.textContent = "Add";
  form.append(input, save);

  add.addEventListener("click", (event) => {
    event.stopPropagation();
    form.hidden = false;
    add.hidden = true;
    input.focus();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const label = input.value.trim();
    if (!label) {
      input.focus();
      return;
    }
    form.hidden = true;
    add.hidden = false;
    input.value = "";
    onAddStep(label, parentId);
  });

  row.append(add, form);
}

/** ⋯ menu: Add here / Suggest structure / Talk about this / Paste structure. */
function attachNodeMenu(
  row: HTMLElement,
  stepId: string,
  onMenuAction?: NodeMenuHandler,
): void {
  const wrap = document.createElement("div");
  wrap.className = "progress-menu-wrap";

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "progress-menu-toggle";
  toggle.textContent = "⋯";
  toggle.title = "Node actions";
  toggle.setAttribute("aria-haspopup", "true");
  toggle.setAttribute("aria-expanded", "false");

  const menu = document.createElement("div");
  menu.className = "progress-menu";
  menu.hidden = true;
  menu.setAttribute("role", "menu");

  for (const action of NODE_MENU_ACTIONS) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "progress-menu-item";
    item.title = action.detail;
    item.dataset.action = action.id;
    item.dataset.stepId = stepId;

    const name = document.createElement("span");
    name.className = "progress-menu-item-label";
    name.textContent = action.label;
    const detail = document.createElement("span");
    detail.className = "progress-menu-item-detail";
    detail.textContent = action.detail;
    item.append(name, detail);

    if (!onMenuAction) {
      item.disabled = true;
    } else {
      item.addEventListener("click", (event) => {
        event.stopPropagation();
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        onMenuAction(action.id, stepId);
      });
    }
    menu.appendChild(item);
  }

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const opening = menu.hidden;
    document.querySelectorAll(".progress-menu").forEach((el) => {
      (el as HTMLElement).hidden = true;
    });
    document.querySelectorAll(".progress-menu-toggle").forEach((el) => {
      el.setAttribute("aria-expanded", "false");
    });
    if (opening) {
      // Fixed to the viewport so overflow on the map cannot clip it.
      const rect = toggle.getBoundingClientRect();
      menu.style.position = "fixed";
      menu.style.left = `${Math.round(rect.left)}px`;
      menu.style.top = `${Math.round(rect.bottom + 4)}px`;
      menu.style.right = "auto";
      menu.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      requestAnimationFrame(() => {
        const box = menu.getBoundingClientRect();
        if (box.bottom > window.innerHeight - 8) {
          menu.style.top = `${Math.max(8, Math.round(rect.top - box.height - 4))}px`;
        }
        if (box.right > window.innerWidth - 8) {
          menu.style.left = `${Math.max(8, Math.round(window.innerWidth - box.width - 8))}px`;
        }
      });
    }
  });

  wrap.append(toggle, menu);
  row.appendChild(wrap);
}

/**
 * Append nested rows under a trunk parent. Hierarchy facts come from
 * familyById — not re-derived from stem string length alone.
 */
function appendAsciiDepth(
  spine: HTMLElement,
  children: PlanningNode[],
  stem: string,
  byId: Map<string, MapFamilyNode>,
  onStepClick?: PlanClickHandler,
  onAddStep?: AddStepHandler,
  onRemoveStep?: RemoveStepHandler,
  selectedId?: string | null,
  onMenuAction?: NodeMenuHandler,
): void {
  children.forEach((child, i) => {
    const isLast = i === children.length - 1;
    const layout = byId.get(child.id);
    const row = document.createElement("div");
    row.className = `progress-row progress-depth-row node-${child.status}`;
    if (layout) {
      applyFamilyAttrs(row, layout);
    } else {
      row.dataset.stepId = child.id;
      row.dataset.depth = String(Math.floor(stem.length / 4) + 1);
    }
    if (selectedId && child.id === selectedId) {
      row.classList.add("is-selected");
    }

    const prefix = document.createElement("span");
    prefix.className = "progress-branch";
    const depth = layout?.depth ?? Math.floor(stem.length / 4) + 1;
    prefix.style.width = indentWidth(depth);
    row.appendChild(prefix);

    const canEdit = PROGRESSION_LIKE.test(child.id);

    if (onStepClick && canEdit) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "progress-bead-btn";
      button.textContent = child.label;
      button.title = "Select this node";
      button.addEventListener("click", () => onStepClick(child.id));
      row.appendChild(button);
    } else {
      const label = document.createElement("span");
      label.className = "progress-bead-label";
      label.textContent = child.label;
      row.appendChild(label);
    }

    if (onRemoveStep && canEdit) {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "progress-remove";
      remove.textContent = "×";
      remove.title = "Remove this node";
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        onRemoveStep(child.id);
      });
      row.appendChild(remove);
    }

    if (onAddStep && canEdit) {
      attachAddControl(row, onAddStep, child.id);
    }

    if (canEdit) {
      attachNodeMenu(row, child.id, onMenuAction);
    }

    spine.appendChild(row);
    if (child.children.length > 0) {
      appendAsciiDepth(
        spine,
        child.children,
        `${stem}${childGuide(!isLast)}`,
        byId,
        onStepClick,
        onAddStep,
        onRemoveStep,
        selectedId,
        onMenuAction,
      );
    }
  });
}

/**
 * Project map as a simple ASCII outline.
 * Optional `identityLabel` (e.g. "#40") sits as the top pole;
 * `rootLabel` is the project name under it — identity ≠ name.
 * Middle nodes nest under the name; nested lines are children.
 * Optional endLabel is a distinct End leaf (omit when it would
 * only repeat the name). + / × steer the map; + on a node nests
 * under that parent. Click selects (no auto-zoom); ⋯ holds
 * Add here / Suggest / Talk about this / Paste structure.
 */
export function treeWordsElement(
  rootLabel: string,
  middle: PlanningNode[],
  onStepClick?: PlanClickHandler,
  onAddStep?: AddStepHandler,
  onRemoveStep?: RemoveStepHandler,
  endLabel?: string | null,
  selectedId?: string | null,
  onMenuAction?: NodeMenuHandler,
  identityLabel?: string | null,
): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.className = "progress-line";

  const spine = document.createElement("div");
  spine.className = "progress-spine";

  const identity = (identityLabel || "").trim();

  if (identity) {
    const idRow = document.createElement("div");
    idRow.className = "progress-row progress-pole progress-pole-identity";
    const idText = document.createElement("span");
    idText.className = "entity-id";
    idText.textContent = identity;
    idText.title = identity;
    idRow.appendChild(idText);
    spine.appendChild(idRow);

    const nameRow = document.createElement("div");
    nameRow.className = "progress-row progress-pole progress-pole-name";
    const namePrefix = document.createElement("span");
    namePrefix.className = "progress-branch";
    namePrefix.style.width = "1.1rem";
    const nameText = document.createElement("span");
    nameText.textContent = rootLabel;
    nameText.title = rootLabel;
    nameRow.append(namePrefix, nameText);
    spine.appendChild(nameRow);
  } else {
    const root = document.createElement("div");
    root.className = "progress-row progress-pole progress-pole-root";
    const rootText = document.createElement("span");
    rootText.textContent = rootLabel;
    rootText.title = rootLabel;
    root.appendChild(rootText);
    spine.appendChild(root);
  }

  const showEnd =
    Boolean(endLabel) &&
    endLabel!.trim().toLowerCase() !== rootLabel.trim().toLowerCase();

  // Live lines from mapLines. Family facts from layoutFamily.
  const layout = layoutFamily(middle);
  const byId = familyById(layout);

  const trunk = document.createElement("div");
  trunk.className = identity
    ? "progress-trunk progress-trunk-under-name"
    : "progress-trunk";

  for (const step of middle) {
    const block = document.createElement("div");
    block.className = "progress-trunk-block";
    const stepLayout = byId.get(step.id);

    const row = document.createElement("div");
    row.className = `progress-row progress-bead node-${step.status}`;
    if (stepLayout) {
      applyFamilyAttrs(row, stepLayout);
    } else {
      row.dataset.stepId = step.id;
      row.dataset.depth = "0";
    }
    if (selectedId && step.id === selectedId) {
      row.classList.add("is-selected");
    }

    const prefix = document.createElement("span");
    prefix.className = "progress-branch";
    prefix.style.width = indentWidth(0);
    row.appendChild(prefix);

    const canEdit = PROGRESSION_LIKE.test(step.id);

    if (onStepClick && canEdit) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "progress-bead-btn";
      button.textContent = step.label;
      button.title = "Select this node";
      button.addEventListener("click", () => onStepClick(step.id));
      row.appendChild(button);
    } else {
      const label = document.createElement("span");
      label.className = "progress-bead-label";
      label.textContent = step.label;
      row.appendChild(label);
    }

    if (onRemoveStep && canEdit) {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "progress-remove";
      remove.textContent = "×";
      remove.title = "Remove this node";
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        onRemoveStep(step.id);
      });
      row.appendChild(remove);
    }

    if (onAddStep && canEdit) {
      attachAddControl(row, onAddStep, step.id);
    }

    if (canEdit) {
      attachNodeMenu(row, step.id, onMenuAction);
    }

    block.appendChild(row);

    if (step.children.length > 0) {
      appendAsciiDepth(
        block,
        step.children,
        childGuide(false),
        byId,
        onStepClick,
        onAddStep,
        onRemoveStep,
        selectedId,
        onMenuAction,
      );
    }
    trunk.appendChild(block);
  }

  if (onAddStep) {
    const addWrap = document.createElement("div");
    addWrap.className = "progress-row progress-add-wrap";

    const prefix = document.createElement("span");
    prefix.className = "progress-branch";
    prefix.style.width = "0.35rem";
    addWrap.appendChild(prefix);
    attachAddControl(addWrap, onAddStep);
    trunk.appendChild(addWrap);
  }

  if (showEnd && endLabel) {
    const end = document.createElement("div");
    end.className = "progress-row progress-pole progress-pole-end";
    const endPrefix = document.createElement("span");
    endPrefix.className = "progress-branch";
    endPrefix.style.width = "0.35rem";
    const endText = document.createElement("span");
    endText.className = "progress-end-label";
    endText.textContent = endLabel;
    endText.title = endLabel;
    end.append(endPrefix, endText);
    trunk.appendChild(end);
  }

  spine.appendChild(trunk);

  wrap.appendChild(spine);
  ensureNodeMenuCloser();
  queueMicrotask(() => installMapLines(wrap));
  return wrap;
}

/** Single document listener for all maps — close ⋯ on outside click. */
let nodeMenuCloserInstalled = false;
function ensureNodeMenuCloser(): void {
  if (nodeMenuCloserInstalled) return;
  nodeMenuCloserInstalled = true;
  document.addEventListener("click", () => {
    document.querySelectorAll(".progress-menu").forEach((el) => {
      (el as HTMLElement).hidden = true;
    });
    document.querySelectorAll(".progress-menu-toggle").forEach((el) => {
      el.setAttribute("aria-expanded", "false");
    });
  });
}
