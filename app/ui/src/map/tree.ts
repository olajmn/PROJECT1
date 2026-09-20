// Renders a PlanningNode tree as nested <ul><li> elements, numbered
// with the same 1. -> i. -> a. convention as
// global-standards/_CONTENT_HIERARCHY.md, applied to the plan tree
// instead of a document's headings. Used by pages/log.ts (Completed
// tab). Projects live map uses treeWords.ts in this same folder
// instead.

import type { PlanningNode } from "../types.js";

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

// 2. Rendering

// `depth` is -1 for the root Goal node (no number - it's a title, not
// a list item); its children (steps) start at depth 0. Optional
// `onStepClick` makes non-root nodes buttons (Active zoom into
// plan.progression); omit it for read-only trees (Log Completed).
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
