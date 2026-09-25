// Block / stack / two-column group layout for the Settings register.

import { el } from "./dom.js";
import { paintLine } from "./paintLine.js";
import type { Block, Group } from "./types.js";

export function arrangeBlock(
  lines: Block,
  className = "settings-block",
): HTMLElement {
  const block = el("div", className);
  for (const line of lines) {
    block.appendChild(paintLine(line));
  }
  return block;
}

/** Single-column stack of blocks (General, Logs). */
export function arrangeStack(blocks: Block[]): HTMLElement {
  const stack = el("div", "settings-register-stack");
  for (const block of blocks) {
    stack.appendChild(arrangeBlock(block));
  }
  return stack;
}

/** Two-column group (Id left, project blocks right). */
export function arrangeGroup(group: Group): HTMLElement {
  const article = el("article", "settings-block settings-block-group");
  if (group.dataSimUserId != null) {
    article.setAttribute("data-sim-user-id", group.dataSimUserId);
  }
  if (group.active) article.classList.add("is-active");

  const row = el("div", "settings-row");
  row.appendChild(arrangeBlock(group.left, "settings-col"));

  const nest = el("div", "settings-nest");
  if (group.right.length === 0) {
    nest.appendChild(el("p", "settings-empty", "No projects"));
  } else {
    for (const projectBlock of group.right) {
      nest.appendChild(arrangeBlock(projectBlock, "settings-block"));
    }
  }
  row.appendChild(nest);
  article.appendChild(row);
  return article;
}
