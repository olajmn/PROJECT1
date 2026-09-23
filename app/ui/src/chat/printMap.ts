// Print the stored map labels into the chat thread. No server, no
// Voice. The tree on the project view is the source.

import type { PlanningNode } from "../types.js";

const MAX_LINES = 400;

export function printMapText(
  root: PlanningNode | null,
  stepId: string | null,
): string {
  if (!root) {
    return "The map is empty.";
  }
  const forest = root.children.length ? root.children : [root];
  if (stepId) {
    const path = findPath(forest, stepId);
    if (path) {
      return pathLines(path);
    }
  }
  const lines: string[] = [];
  collect(forest, 0, lines);
  return lines.length ? lines.slice(0, MAX_LINES).join("\n") : "The map is empty.";
}

function findPath(
  steps: PlanningNode[],
  stepId: string,
): PlanningNode[] | null {
  for (const step of steps) {
    if (step.id === stepId) {
      return [step];
    }
    const rest = findPath(step.children, stepId);
    if (rest) {
      return [step, ...rest];
    }
  }
  return null;
}

function pathLines(path: PlanningNode[]): string {
  const lines: string[] = [];
  path.slice(0, -1).forEach((step, depth) => {
    const label = step.label.trim();
    if (label) {
      lines.push(`${"  ".repeat(depth)}${label}`);
    }
  });
  const last = path[path.length - 1];
  const start = Math.max(path.length - 1, 0);
  collect([last], start, lines);
  return lines.slice(0, MAX_LINES).join("\n");
}

function collect(
  steps: PlanningNode[],
  depth: number,
  lines: string[],
): void {
  for (const step of steps) {
    const label = step.label.trim();
    if (label) {
      lines.push(`${"  ".repeat(depth)}${label}`);
    }
    if (step.children.length) {
      collect(step.children, depth + 1, lines);
    }
  }
}
