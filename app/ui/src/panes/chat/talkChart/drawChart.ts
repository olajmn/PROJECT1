// Beads for one chat chart. Same drawing as the file map
// (`treeWordsElement`); not written into plan.progression.
//
// Contents
//  1. Ids
//      - chartId()
//      - openChartId()
//  2. renderChartTree()

import type { MapNode, TalkChartEntry } from "../../../dataShapes.js";
import { NEST_INSET_REM } from "../../canvas/spacing.js";
import { treeWordsElement } from "../../canvas/drawNodes.js";

// 1. Ids

export function chartId(start: number): string {
  return `t${start}`;
}

export function openChartId(sequences: TalkChartEntry[]): string | undefined {
  for (const sequence of sequences) {
    if (sequence.open) return chartId(sequence.start);
    const nested = openChartId(sequence.children);
    if (nested) return nested;
  }
  return undefined;
}

function toNodes(sequences: TalkChartEntry[]): MapNode[] {
  return sequences.map((sequence) => ({
    id: chartId(sequence.start),
    label: sequence.label,
    status: sequence.open ? "current" : "open",
    children: toNodes(sequence.children),
  }));
}

function findSequence(
  sequences: TalkChartEntry[],
  stepId: string,
): TalkChartEntry | null {
  for (const sequence of sequences) {
    if (chartId(sequence.start) === stepId) return sequence;
    const nested = findSequence(sequence.children, stepId);
    if (nested) return nested;
  }
  return null;
}

// 2. renderChartTree()

export function renderChartTree(
  sequences: TalkChartEntry[],
  selectedId: string | undefined,
  onPick: (sequence: TalkChartEntry) => void,
): HTMLDivElement {
  const tree = treeWordsElement(
    "Talk",
    toNodes(sequences),
    (stepId) => {
      const sequence = findSequence(sequences, stepId);
      if (sequence) onPick(sequence);
    },
    undefined,
    undefined,
    selectedId,
  );
  const trunk = tree.querySelector(".progress-trunk");
  if (trunk instanceof HTMLElement) {
    // Spine under the title, tick into the first beads — same nest
    // as the file map. Depth-0 indent alone sits on the spine.
    trunk.style.marginLeft = `${NEST_INSET_REM}rem`;
  }
  return tree;
}
