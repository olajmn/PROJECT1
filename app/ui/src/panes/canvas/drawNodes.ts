/**
 * Write the words on the live project map (DOM rows + controls).
 * Layout: [[surfaces]] § 4 — `#N` → title → spine beads; depth under beads.
 * Who-under-who from nodeFamily; lines from mapLines; indent from spacing.ts.
 */

import type { MapNode } from "../../dataShapes.js";
import { indentRem, NEST_INSET_REM } from "./spacing.js";
import { installMapLines } from "./lines/addLines.js";
import {
  applyFamilyAttrs,
  familyById,
  layoutFamily,
  type MapFamilyNode,
} from "./nodeFamily.js";

export type PlanClickHandler = (stepId: string) => void;
/** parentId omitted/undefined = add at project root. */
export type AddStepHandler = (label: string, parentId?: string) => void;
export type RemoveStepHandler = (stepId: string) => void;
export type NodeMenuActionId =
  | "register"
  | "remove"
  | "suggest"
  | "analyze"
  | "paste"
  | "save_tree"
  | "insert_tree";
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
    id: "remove",
    label: "Remove",
    detail: "Delete this node from the map.",
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
  {
    id: "save_tree",
    label: "Save as tree",
    detail: "Keep this node and everything under it as a reusable structure.",
  },
  {
    id: "insert_tree",
    label: "Insert saved tree…",
    detail: "Add one of your saved trees under this node as new nodes.",
  },
];

const PROGRESSION_LIKE = /^p\d+$/;

function childGuide(_parentContinues: boolean): string {
  // Indent width only; SVG draws connectors. Kept for stem length → depth.
  return "    ";
}

function indentWidth(depth: number): string {
  return indentRem(depth);
}

/** Inline + form that calls onAddStep(label, parentId).
 *  `showButton: false` keeps only the hidden form (opened via ⋯ Add here). */
function attachAddControl(
  host: HTMLElement,
  onAddStep: AddStepHandler,
  parentId?: string,
  opts?: { showButton?: boolean },
): void {
  const showButton = opts?.showButton !== false;

  const add = document.createElement("button");
  add.type = "button";
  add.className = "progress-add progress-add-inline";
  add.textContent = "+";
  add.title = parentId
    ? "Add a node under this one"
    : "Add a node under the project";
  if (!showButton) add.hidden = true;

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
  // Keep focus in the input on Add: Safari does not focus a clicked
  // button, so focusout would cancel the form before submit fires.
  save.addEventListener("mousedown", (event) => event.preventDefault());

  const openForm = () => {
    form.hidden = false;
    add.hidden = true;
    input.focus();
  };

  // Escape, an empty Add, or focus leaving the form cancels — the
  // form must never trap the user into typing a name.
  const closeForm = () => {
    form.hidden = true;
    if (showButton) add.hidden = false;
    input.value = "";
  };
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeForm();
  });
  form.addEventListener("focusout", (event) => {
    const next = event.relatedTarget as Node | null;
    if (!next || !form.contains(next)) closeForm();
  });

  add.addEventListener("click", (event) => {
    event.stopPropagation();
    openForm();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const label = input.value.trim();
    closeForm();
    if (label) onAddStep(label, parentId);
  });

  // Menu “Add here” finds this to open the form without a visible +.
  form.dataset.addForm = "1";

  host.append(add, form);
}

/** Square around label + ⋯ (indent stays outside). + / × live in the menu. */
function fillBeadUnit(
  row: HTMLElement,
  node: MapNode,
  onStepClick?: PlanClickHandler,
  onAddStep?: AddStepHandler,
  _onRemoveStep?: RemoveStepHandler,
  onMenuAction?: NodeMenuHandler,
): void {
  const unit = document.createElement("div");
  unit.className = "progress-bead-unit";

  const canEdit = PROGRESSION_LIKE.test(node.id);

  if (onStepClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "progress-bead-btn";
    button.textContent = node.label;
    button.title = "Talk about this";
    button.addEventListener("click", () => onStepClick(node.id));
    unit.appendChild(button);
  } else {
    const label = document.createElement("span");
    label.className = "progress-bead-label";
    label.textContent = node.label;
    unit.appendChild(label);
  }

  if (onAddStep && canEdit) {
    attachAddControl(unit, onAddStep, node.id, { showButton: false });
  }

  if (canEdit && onMenuAction) {
    attachNodeMenu(unit, node.id, onMenuAction);
  }

  row.appendChild(unit);
}

/** ⋯ menu: Add here / Remove / Suggest / Talk / Paste / saved trees. */
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

    item.textContent = action.label;

    if (!onMenuAction) {
      item.disabled = true;
    } else {
      item.addEventListener("click", (event) => {
        event.stopPropagation();
        closeNodeMenu();
        onMenuAction(action.id, stepId);
      });
    }
    menu.appendChild(item);
  }

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const opening = menu.hidden;
    closeNodeMenu();
    if (opening) {
      // The map stage is CSS-transformed (pan/zoom), which makes it the
      // containing block for position: fixed — so the open menu lives on
      // <body>, where viewport coordinates mean the viewport.
      document.body.appendChild(menu);
      openNodeMenu = { menu, toggle, home: wrap };
      const rect = toggle.getBoundingClientRect();
      menu.style.left = `${Math.round(rect.left)}px`;
      menu.style.top = `${Math.round(rect.bottom + 4)}px`;
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
  children: MapNode[],
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

    fillBeadUnit(
      row,
      child,
      onStepClick,
      onAddStep,
      onRemoveStep,
      onMenuAction,
    );

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
 * Project map: `#N` → title → waypoints ([[surfaces]] § 4).
 * Id and title are header beads (same box language as tree beads, but
 * not progression nodes — no ⋯). Middle = root children; nested = depth.
 */
export function treeWordsElement(
  nameLabel: string,
  middle: MapNode[],
  onStepClick?: PlanClickHandler,
  onAddStep?: AddStepHandler,
  onRemoveStep?: RemoveStepHandler,
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
    const idUnit = document.createElement("div");
    idUnit.className = "progress-bead-unit progress-header-unit";
    const idText = document.createElement("span");
    idText.className = "entity-id";
    idText.textContent = identity;
    idText.title = identity;
    idUnit.appendChild(idText);
    idRow.appendChild(idUnit);
    spine.appendChild(idRow);
  }

  const nameRow = document.createElement("div");
  nameRow.className = "progress-row progress-pole progress-pole-name";
  if (identity) {
    const namePrefix = document.createElement("span");
    namePrefix.className = "progress-branch";
    // Sit on the nest spine under #N (inset), then a short tick into the box.
    namePrefix.style.width = `${NEST_INSET_REM}rem`;
    nameRow.appendChild(namePrefix);
  }
  const nameUnit = document.createElement("div");
  nameUnit.className = "progress-bead-unit progress-header-unit";
  const nameText = document.createElement("span");
  nameText.className = "progress-name-label";
  nameText.textContent = nameLabel;
  nameText.title = nameLabel;
  nameUnit.appendChild(nameText);
  nameRow.appendChild(nameUnit);
  spine.appendChild(nameRow);

  const layout = layoutFamily(middle);
  const byId = familyById(layout);

  const trunk = document.createElement("div");
  // Under the title nest: 2× inset so spine + tick land on bead left edges.
  trunk.className = identity
    ? "progress-trunk progress-trunk-under-name"
    : "progress-trunk";
  if (identity) {
    trunk.style.marginLeft = `${2 * NEST_INSET_REM}rem`;
  }

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

    fillBeadUnit(
      row,
      step,
      onStepClick,
      onAddStep,
      onRemoveStep,
      onMenuAction,
    );

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
    prefix.style.width = indentWidth(0);
    addWrap.appendChild(prefix);
    attachAddControl(addWrap, onAddStep);
    trunk.appendChild(addWrap);
  }

  spine.appendChild(trunk);

  wrap.appendChild(spine);
  ensureNodeMenuCloser();
  queueMicrotask(() => installMapLines(wrap));
  return wrap;
}

/** The one open ⋯ menu, parked on <body> until it closes. */
let openNodeMenu: {
  menu: HTMLElement;
  toggle: HTMLElement;
  home: HTMLElement;
} | null = null;

function closeNodeMenu(): void {
  if (!openNodeMenu) return;
  const { menu, toggle, home } = openNodeMenu;
  menu.hidden = true;
  toggle.setAttribute("aria-expanded", "false");
  home.appendChild(menu);
  openNodeMenu = null;
}

/** Single set of document listeners for all maps — close ⋯ on outside
 *  click, Escape, or anything that moves the map under it. */
let nodeMenuCloserInstalled = false;
function ensureNodeMenuCloser(): void {
  if (nodeMenuCloserInstalled) return;
  nodeMenuCloserInstalled = true;
  document.addEventListener("click", closeNodeMenu);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeNodeMenu();
  });
  document.addEventListener("wheel", closeNodeMenu, { passive: true });
  window.addEventListener("resize", closeNodeMenu);
}
