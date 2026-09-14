// The Steps page - a workbench for the recursive Step model
// (backend/planning/plan/step.py), where a typed goal becomes one
// root Step and every level below it is expanded only when clicked.
// Existing pages render a plan record's fixed two levels; this one
// renders whatever depth the tree actually has, so the on-demand
// depth idea can be looked at instead of only argued about (see
// docs/planning-model.md § Adaptive depth).
//
// Its own renderer rather than tree.ts's renderNode(): every step
// here is a clickable control with per-step state, which renderNode()
// has no notion of. The numbering convention IS shared, via
// tree.ts's treeLabel(), so this page can't drift from the
// 1. -> i. -> a. rule the others follow.
//
// Nothing on this page is persisted - the server holds one scratch
// tree in memory (server.py § 1) and it is gone on restart.

// Contents
//  1. Status line
//      - setStatus()
//  2. Rendering
//      - zoomHint()
//      - renderStep()
//      - renderTree()
//  3. Actions
//      - build()
//      - zoom()
//  4. Initialization

import { createTree, fetchTree, zoomStep } from "./api.js";
import { initNavCounts } from "./nav.js";
import { treeLabel } from "./tree.js";
import type { StepNode, TreeView } from "./types.js";

const form = document.getElementById("tree-form") as HTMLFormElement;
const input = document.getElementById("tree-input") as HTMLInputElement;
const statusLine = document.getElementById("status") as HTMLParagraphElement;
const container = document.getElementById("tree") as HTMLDivElement;

let current: TreeView | null = null;
// Blocks overlapping zooms: the server keeps ONE tree and every
// response is the whole of it, so two in-flight calls would race to
// overwrite each other's render.
let busy = false;

// 1. Status line

function setStatus(text: string): void {
  statusLine.hidden = text === "";
  statusLine.textContent = text;
}

// 2. Rendering

/** What clicking this step would mean - a childless step reads very
 * differently depending on whether it has been zoomed yet, and that
 * distinction is the whole point of the page. */
function zoomHint(step: StepNode): string {
  if (step.children.length > 0) return "re-zoom";
  return step.zoomed ? "actionable - nothing under it" : "zoom";
}

function renderStep(step: StepNode, depth: number, index: number): HTMLLIElement {
  const li = document.createElement("li");
  li.className = `node node-${step.status}`;

  const button = document.createElement("button");
  button.type = "button";
  button.className = "step-zoom";
  button.disabled = busy;
  button.textContent = depth >= 0 ? `${treeLabel(depth, index)} ${step.label}` : step.label;
  button.title = zoomHint(step);
  button.addEventListener("click", () => void zoom(step.id));
  li.appendChild(button);

  if (step.zoomed && step.children.length === 0) {
    const leaf = document.createElement("span");
    leaf.className = "history-key";
    leaf.textContent = " (actionable)";
    li.appendChild(leaf);
  }

  if (step.children.length > 0) {
    const list = document.createElement("ul");
    step.children.forEach((child, i) => {
      list.appendChild(renderStep(child, depth + 1, i));
    });
    li.appendChild(list);
  }
  return li;
}

function renderTree(): void {
  container.innerHTML = "";
  if (!current?.root) return;

  // Same `depth === -1` convention as tree.ts: the root is a title,
  // not a numbered list item, so its children start the numbering.
  const wrap = document.createElement("div");
  wrap.className = "plan";
  const list = document.createElement("ul");
  list.appendChild(renderStep(current.root, -1, 0));
  wrap.appendChild(list);
  container.appendChild(wrap);
}

// 3. Actions

async function build(text: string): Promise<void> {
  busy = true;
  setStatus("building...");
  try {
    current = await createTree(text);
    setStatus(`timeframe: ${current.duration} - click any step to zoom into it`);
  } catch (err) {
    current = null;
    setStatus((err as Error).message);
  } finally {
    busy = false;
    renderTree();
  }
}

async function zoom(stepId: string): Promise<void> {
  if (busy) return;
  busy = true;
  setStatus("zooming...");
  renderTree(); // repaint with every button disabled
  try {
    current = await zoomStep(stepId);
    setStatus(`timeframe: ${current.duration} - click any step to zoom into it`);
  } catch (err) {
    setStatus((err as Error).message);
  } finally {
    busy = false;
    renderTree();
  }
}

// 4. Initialization

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (text) void build(text);
});

// Restore the server's existing tree, if any - leaving this page and
// coming back must not throw away work that cost two model calls per
// level (see fetchTree()).
fetchTree()
  .then((view) => {
    if (!view.root) return;
    current = view;
    input.value = view.root.label;
    setStatus(`timeframe: ${view.duration} - click any step to zoom into it`);
    renderTree();
  })
  .catch(() => {
    // No tree to restore is the normal first-visit case, not an
    // error worth showing.
  });

initNavCounts();
