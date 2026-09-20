// Block / stack / two-column group layout.

import { el } from "./dom.js";
import { renderPara } from "./templates.js";
import type { Block, Group } from "./types.js";

export function renderBlock(
  paras: Block,
  className = "settings-block",
): HTMLElement {
  const block = el("div", className);
  for (const para of paras) {
    block.appendChild(renderPara(para));
  }
  return block;
}

/** Single-column stack of blocks (General, Logs). */
export function renderStack(blocks: Block[]): HTMLElement {
  const stack = el("div", "settings-register-stack");
  for (const block of blocks) {
    stack.appendChild(renderBlock(block));
  }
  return stack;
}

/** Two-column group (Directory: Id left, project blocks right). */
export function renderGroup(group: Group): HTMLElement {
  const article = el("article", "settings-block settings-block-group");
  if (group.dataSimUserId != null) {
    article.setAttribute("data-sim-user-id", group.dataSimUserId);
  }
  if (group.active) article.classList.add("is-active");

  const row = el("div", "settings-row");
  row.appendChild(renderBlock(group.left, "settings-col"));

  const nest = el("div", "settings-nest");
  if (group.right.length === 0) {
    nest.appendChild(el("p", "settings-empty", "No projects"));
  } else {
    for (const projectBlock of group.right) {
      nest.appendChild(renderBlock(projectBlock, "settings-block"));
    }
  }
  row.appendChild(nest);
  article.appendChild(row);
  return article;
}
