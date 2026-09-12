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

function treeLabel(depth: number, index: number): string {
  if (depth === 0) return `${index + 1}.`;
  if (depth === 1) return `${ROMAN_NUMERALS[index] ?? String(index + 1)}.`;
  // Depth 2+ isn't produced by today's data (steps -> microsteps is
  // one level deep only), but falls back to letters rather than
  // breaking if that ever changes.
  return `${String.fromCharCode(97 + (index % 26))}.`;
}

// 2. Rendering

// `depth` is -1 for the root Goal node (no number - it's a title, not
// a list item); its children (steps) start at depth 0, their children
// (microsteps) at depth 1. `index` is this node's position among its
// own siblings, passed in by the caller rather than tracked globally,
// so numbering restarts under every parent - same rule
// _CONTENT_HIERARCHY.md states for document headings.
export function renderNode(node: PlanningNode, depth: number, index: number): HTMLLIElement {
  const li = document.createElement("li");
  li.className = `node node-${node.status}`;
  li.textContent = depth >= 0 ? `${treeLabel(depth, index)} ${node.label}` : node.label;
  if (node.children.length > 0) {
    const list = document.createElement("ul");
    node.children.forEach((child, i) => {
      list.appendChild(renderNode(child, depth + 1, i));
    });
    li.appendChild(list);
  }
  return li;
}

/** A `.plan` wrapper around `renderNode(node, -1, 0)` - the same
 * markup shape appendPlan() in main.ts builds inline, factored out so
 * active.ts can produce an identical plan block per goal card. */
export function planElement(node: PlanningNode): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.className = "plan";
  const list = document.createElement("ul");
  list.appendChild(renderNode(node, -1, 0));
  wrap.appendChild(list);
  return wrap;
}
