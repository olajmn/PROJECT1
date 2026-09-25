/**
 * Copy the project map as ordinary text (classic ASCII tree).
 * Built from nodeFamily — same who-under-who as the live map.
 */

import type { MapNode } from "../../dataShapes.js";
import {
  asciiStem,
  layoutFamily,
  type MapFamilyNode,
} from "./nodeFamily.js";

function branch(isLast: boolean): string {
  return isLast ? "└── " : "├── ";
}

function fullStem(node: MapFamilyNode, underName: boolean): string {
  return underName ? `    ${asciiStem(node)}` : asciiStem(node);
}

function pushAir(lines: string[], stem: string): void {
  lines.push(`${stem}│`);
  lines.push(`${stem}│`);
}

function parentOf(
  layout: MapFamilyNode[],
  node: MapFamilyNode,
): MapFamilyNode | null {
  if (!node.parentId) return null;
  return layout.find((n) => n.id === node.parentId) ?? null;
}

/** Full map as a monospace tree string (identity + name + middle). */
export function copyAsText(
  name: string,
  middle: MapNode[],
  identityLabel?: string | null,
  options?: { airBetweenSiblings?: boolean },
): string {
  const air = options?.airBetweenSiblings !== false;
  const lines: string[] = [];
  const identity = (identityLabel || "").trim();
  const underName = Boolean(identity);
  const layout = layoutFamily(middle);

  if (identity) {
    lines.push(identity);
    lines.push(`${branch(true)}${name}`);
  } else {
    lines.push(name);
  }

  for (let i = 0; i < layout.length; i++) {
    const n = layout[i];
    const stem = fullStem(n, underName);
    lines.push(`${stem}${branch(n.isLastSibling)}${n.label}`);

    if (!air) continue;

    const nextDepth =
      i + 1 < layout.length ? layout[i + 1].depth : -1;

    // Leaf with a following sibling: air before that sibling.
    if (!n.hasChildren && !n.isLastSibling) {
      pushAir(lines, stem);
      continue;
    }

    // Leaving a subtree: air for each finished parent that continues.
    if (n.depth > nextDepth) {
      let cur: MapFamilyNode | null = n;
      while (cur && cur.depth > nextDepth) {
        if (cur.isLastSibling) {
          const parent = parentOf(layout, cur);
          if (parent && !parent.isLastSibling) {
            pushAir(lines, fullStem(parent, underName));
          }
          cur = parent;
        } else {
          break;
        }
      }
    }
  }

  return lines.join("\n");
}
