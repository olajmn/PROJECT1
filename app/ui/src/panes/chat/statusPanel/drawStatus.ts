// Draws a project's status: summary rows, then a day-by-day change
// pulse (chat excluded). Node names in the summary become buttons that
// select that node on the map.
//
// Contents
//  1. drawStatus()
//  2. Clickable node names
//      - withNodeButtons()

import type { ProjectStatus } from "../../../dataShapes.js";

// 1. drawStatus()

export function drawStatus(
  status: ProjectStatus,
  onNode: (label: string) => void,
): HTMLElement {
  const root = document.createElement("div");
  root.className = "status";

  const summary = document.createElement("dl");
  summary.className = "status-summary";
  for (const row of status.summary) {
    const label = document.createElement("dt");
    label.textContent = row.label;
    const value = document.createElement("dd");
    value.append(...withNodeButtons(row.text, row.nodes, onNode));
    summary.append(label, value);
  }
  root.append(summary);

  if (status.history.length > 0) {
    const heading = document.createElement("p");
    heading.className = "status-heading";
    heading.textContent = "Changes";
    root.append(heading);
  }

  const list = document.createElement("ul");
  list.className = "status-lines status-days";
  for (const line of status.history) {
    const item = document.createElement("li");
    const day = document.createElement("span");
    day.className = "status-day-label";
    day.textContent = line.day;
    const text = document.createElement("span");
    text.className = "status-text";
    text.textContent = line.text;
    if (line.changes === 0) {
      item.classList.add("is-quiet");
    }
    item.append(day, text);
    list.append(item);
  }
  if (status.history.length > 0) {
    root.append(list);
  }

  if (status.earlier > 0) {
    const earlier = document.createElement("p");
    earlier.className = "status-earlier";
    earlier.textContent = `… ${status.earlier} earlier days`;
    root.append(earlier);
  }
  return root;
}

// 2. Clickable node names

/** `text` split into plain text and buttons, one button per mention of a
 * name in `nodes` (longest names first, so "Roof tiles" wins over "Roof"). */
function withNodeButtons(
  text: string,
  nodes: string[],
  onNode: (label: string) => void,
): Node[] {
  const names = [...new Set(nodes.filter(Boolean))].sort((a, b) => b.length - a.length);
  if (names.length === 0) return [document.createTextNode(text)];
  const escaped = names.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`));
  return parts
    .filter((part) => part !== "")
    .map((part) => {
      if (!names.includes(part)) return document.createTextNode(part);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "status-node";
      button.textContent = part;
      button.title = `Select "${part}" on the map`;
      button.addEventListener("click", () => onNode(part));
      return button;
    });
}
