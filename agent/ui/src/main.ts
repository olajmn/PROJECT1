// DOM wiring for the agent/ conversation prototype. Deliberately one
// small file: appending chat messages and rendering an optional
// PlanningNode tree are the whole job here - no framework, no state
// library, no routing (see docs/v4-migration-decision.md, UI Manifestation).

import { sendMessage } from "./api.js";
import type { PlanningNode } from "./types.js";

const transcript = document.getElementById("transcript") as HTMLDivElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;

function appendMessage(who: "You" | "Agent", text: string): void {
  const row = document.createElement("div");
  row.className = `message message-${who.toLowerCase()}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who;
  const body = document.createElement("span");
  body.className = "text";
  body.textContent = text;
  row.append(label, body);
  transcript.appendChild(row);
  transcript.scrollTop = transcript.scrollHeight;
}

// Same 1. -> i. -> a. convention as global-standards/_CONTENT_HIERARCHY.md,
// applied to the plan tree instead of a document's headings. Computed
// purely from each node's position among its siblings - never stored
// in the data or written by the model (see plan_structure.py's own
// docstring for why: baking "1." into a label would duplicate the
// list's own order and drift the moment steps are added or removed).
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

// `depth` is -1 for the root Goal node (no number - it's a title, not
// a list item); its children (steps) start at depth 0, their children
// (microsteps) at depth 1. `index` is this node's position among its
// own siblings, passed in by the caller rather than tracked globally,
// so numbering restarts under every parent - same rule
// _CONTENT_HIERARCHY.md states for document headings.
function renderNode(node: PlanningNode, depth: number, index: number): HTMLLIElement {
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

function appendPlan(node: PlanningNode): void {
  const wrap = document.createElement("div");
  wrap.className = "plan";
  const list = document.createElement("ul");
  list.appendChild(renderNode(node, -1, 0));
  wrap.appendChild(list);
  transcript.appendChild(wrap);
  transcript.scrollTop = transcript.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage("You", text);
  input.value = "";
  input.disabled = true;

  try {
    const result = await sendMessage(text);
    appendMessage("Agent", result.reply);
    if (result.node) {
      appendPlan(result.node);
    }
  } catch (err) {
    appendMessage("Agent", `(error: ${(err as Error).message})`);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

input.focus();
