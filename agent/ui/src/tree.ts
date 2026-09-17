// Renders a PlanningNode tree as nested <ul><li> elements, numbered
// with the same 1. -> i. -> a. convention as
// global-standards/_CONTENT_HIERARCHY.md, applied to the plan tree
// instead of a document's headings. Shared by main.ts (the free-
// conversation chat) and active.ts (the Active page) - one place
// producing this markup, not two implementations drifting apart.
//
// Numbering is computed purely from each node's position among its
// siblings - never stored in the data or written by the model (see
// backend/planning/plan/plan_structure.py's own docstring for why
// baking "1." into a label would duplicate the list's own order and
// drift the moment steps are added or removed).

// Contents
//  1. Numbering
//      - ROMAN_NUMERALS
//      - treeLabel()
//  2. Rendering
//      - renderNode()
//      - planElement()

import type { PlanningNode } from "./types.js";

// 1. Numbering

const ROMAN_NUMERALS = [
  "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
  "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx",
];

export function treeLabel(depth: number, index: number): string {
  if (depth === 0) return `${index + 1}.`;
  if (depth === 1) return `${ROMAN_NUMERALS[index] ?? String(index + 1)}.`;
  // Depth 2+ falls back to letters rather than breaking.
  return `${String.fromCharCode(97 + (index % 26))}.`;
}

export type PlanClickHandler = (stepId: string) => void;
export type AddStepHandler = (label: string) => void;
export type RemoveStepHandler = (stepId: string) => void;

// 2. Rendering

// `depth` is -1 for the root Goal node (no number - it's a title, not
// a list item); its children (steps) start at depth 0. Optional
// `onStepClick` makes non-root nodes buttons (Active zoom into
// plan.progression); omit it for read-only trees (Conversation).
export function renderNode(
  node: PlanningNode,
  depth: number,
  index: number,
  onStepClick?: PlanClickHandler,
): HTMLLIElement {
  const li = document.createElement("li");
  li.className = `node node-${node.status}`;
  const text = depth >= 0 ? `${treeLabel(depth, index)} ${node.label}` : node.label;

  if (depth >= 0 && onStepClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "step-zoom";
    button.textContent = text;
    button.title = "Look closer at this step";
    button.addEventListener("click", () => onStepClick(node.id));
    li.appendChild(button);
  } else {
    li.textContent = text;
  }

  if (node.children.length > 0) {
    const list = document.createElement("ul");
    node.children.forEach((child, i) => {
      list.appendChild(renderNode(child, depth + 1, i, onStepClick));
    });
    li.appendChild(list);
  }
  return li;
}

/** A `.plan` wrapper around `renderNode(node, -1, 0)`. */
export function planElement(
  node: PlanningNode,
  onStepClick?: PlanClickHandler,
): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.className = "plan";
  const list = document.createElement("ul");
  list.appendChild(renderNode(node, -1, 0, onStepClick));
  wrap.appendChild(list);
  return wrap;
}

const PROGRESSION_LIKE = /^p\d+$/;

/**
 * Progress line stub: Start — middle Steps — End.
 * Middle nodes are the root's children (progression steps). Depth
 * under a bead is that step's children (zoom). Poles are not zoomable.
 */
export function progressLineElement(
  endLabel: string,
  middle: PlanningNode[],
  onStepClick?: PlanClickHandler,
  onAddStep?: AddStepHandler,
  onRemoveStep?: RemoveStepHandler,
): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.className = "progress-line";

  const spine = document.createElement("div");
  spine.className = "progress-spine";

  const start = document.createElement("div");
  start.className = "progress-pole progress-pole-start";
  start.textContent = "Start";
  spine.appendChild(start);

  for (const step of middle) {
    const bead = document.createElement("div");
    bead.className = `progress-bead node-${step.status}`;

    const head = document.createElement("div");
    head.className = "progress-bead-head";

    if (onStepClick && PROGRESSION_LIKE.test(step.id)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "progress-bead-btn";
      button.textContent = step.label;
      button.title = "Look closer at this step";
      button.addEventListener("click", () => onStepClick(step.id));
      head.appendChild(button);
    } else {
      const label = document.createElement("div");
      label.className = "progress-bead-label";
      label.textContent = step.label;
      head.appendChild(label);
    }

    if (onRemoveStep && PROGRESSION_LIKE.test(step.id)) {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "progress-remove";
      remove.textContent = "×";
      remove.title = "Remove this step";
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        onRemoveStep(step.id);
      });
      head.appendChild(remove);
    }

    bead.appendChild(head);
    if (step.children.length > 0) {
      const depth = document.createElement("ul");
      depth.className = "progress-depth";
      step.children.forEach((child, i) => {
        depth.appendChild(renderNode(child, 1, i, onStepClick));
      });
      bead.appendChild(depth);
    }
    spine.appendChild(bead);
  }

  if (onAddStep) {
    const addWrap = document.createElement("div");
    addWrap.className = "progress-add-wrap";

    const add = document.createElement("button");
    add.type = "button";
    add.className = "progress-add";
    add.textContent = "+";
    add.title = "Add a step you name";

    const form = document.createElement("form");
    form.className = "progress-add-form";
    form.hidden = true;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "progress-add-input";
    input.placeholder = "Step name…";
    input.autocomplete = "off";
    const save = document.createElement("button");
    save.type = "submit";
    save.textContent = "Add";
    form.append(input, save);

    add.addEventListener("click", () => {
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
      onAddStep(label);
    });

    addWrap.append(add, form);
    spine.appendChild(addWrap);
  }

  const end = document.createElement("div");
  end.className = "progress-pole progress-pole-end";
  end.textContent = endLabel;
  end.title = endLabel;
  spine.appendChild(end);

  wrap.appendChild(spine);
  return wrap;
}
