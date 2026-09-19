/**
 * Who-under-who for the project map (parent / sibling / depth).
 * mapLines and copyAsText consume this; they don't re-derive hierarchy.
 */

import type { PlanningNode } from "../types.js";

/** One node as the drawer/exporter needs to understand it. */
export interface MapFamilyNode {
  id: string;
  label: string;
  status: PlanningNode["status"];
  /** 0 = under project name; 1+ = nested. */
  depth: number;
  /** null = direct child of the project name. */
  parentId: string | null;
  siblingIndex: number;
  siblingCount: number;
  isLastSibling: boolean;
  hasChildren: boolean;
  /** Same as hasChildren — can be a parent. */
  isParent: boolean;
  /** depth > 0 — can be a child. */
  isChild: boolean;
  /**
   * For each ancestor from root toward parent: whether that ancestor
   * still has later siblings (classic ASCII │ column).
   */
  ancestorContinues: boolean[];
}

/** Flat, pre-order walk of the progression middle tree. */
export function layoutFamily(
  middle: PlanningNode[],
  parentId: string | null = null,
  depth = 0,
  ancestorContinues: boolean[] = [],
): MapFamilyNode[] {
  const out: MapFamilyNode[] = [];
  const count = middle.length;
  middle.forEach((node, i) => {
    const isLast = i === count - 1;
    const hasChildren = node.children.length > 0;
    const entry: MapFamilyNode = {
      id: node.id,
      label: node.label,
      status: node.status,
      depth,
      parentId,
      siblingIndex: i,
      siblingCount: count,
      isLastSibling: isLast,
      hasChildren,
      isParent: hasChildren,
      isChild: depth > 0,
      ancestorContinues: ancestorContinues.slice(),
    };
    out.push(entry);
    if (hasChildren) {
      out.push(
        ...layoutFamily(node.children, node.id, depth + 1, [
          ...ancestorContinues,
          !isLast,
        ]),
      );
    }
  });
  return out;
}

/** Index by id for DOM / SVG lookups. */
export function familyById(
  layout: MapFamilyNode[],
): Map<string, MapFamilyNode> {
  return new Map(layout.map((n) => [n.id, n]));
}

/** Stamp structural attrs on a map row element. */
export function applyFamilyAttrs(
  row: HTMLElement,
  node: MapFamilyNode,
): void {
  row.dataset.stepId = node.id;
  row.dataset.depth = String(node.depth);
  row.dataset.parentId = node.parentId ?? "";
  row.dataset.siblingIndex = String(node.siblingIndex);
  row.dataset.isLast = node.isLastSibling ? "1" : "0";
  row.dataset.hasChildren = node.hasChildren ? "1" : "0";
  row.dataset.isParent = node.isParent ? "1" : "0";
  row.dataset.isChild = node.isChild ? "1" : "0";
}

/** Classic ASCII stem before ├── / └── for this family node. */
export function asciiStem(node: MapFamilyNode): string {
  return node.ancestorContinues
    .map((continues) => (continues ? "│   " : "    "))
    .join("");
}
