/**
 * Paint nest spines for Text (ticks into beads) or Line (word bars).
 * Same topology — [[ui]] § 2; geometry from spacing.ts.
 */

import { NEST_INSET_PX } from "../spacing.js";
import { MIN_WORD_PX } from "../lineView/thresholds.js";
import {
  beadAnchor,
  midY,
  stroke,
  wrapScale,
  type BeadAnchor,
} from "./svgHelpers.js";

export type LinePaintMode = "text" | "line";

const SPINE = "progress-svg-stroke";
const LINE_SPINE = "progress-svg-stroke progress-svg-diagram";
const LINE_WORD =
  "progress-svg-stroke progress-svg-diagram progress-svg-word";

/** Tick from spine to bead left (Text), or tick + word-bar (Line). */
function paintNode(
  svg: SVGElement,
  spineX: number,
  y: number,
  box: BeadAnchor,
  mode: LinePaintMode,
): void {
  if (box.left > spineX) {
    stroke(
      svg,
      spineX,
      y,
      box.left,
      y,
      mode === "line" ? LINE_SPINE : SPINE,
    );
  }
  if (mode === "line") {
    const bar = Math.max(box.width, MIN_WORD_PX);
    stroke(svg, box.left, y, box.left + bar, y, LINE_WORD);
  }
}

/**
 * Paint the tree overlay into a cleared SVG.
 * Text: nest drops from box bottom. Line: joins at midY (word-bar).
 */
export function paintMapNest(
  wrap: HTMLElement,
  svg: SVGElement,
  mode: LinePaintMode,
): void {
  const scale = wrapScale(wrap);
  const origin = wrap.getBoundingClientRect();
  const trunk = wrap.querySelector(".progress-trunk") as HTMLElement | null;
  if (!trunk) return;

  const cls = mode === "line" ? LINE_SPINE : SPINE;
  const idRow = wrap.querySelector(
    ".progress-pole-identity",
  ) as HTMLElement | null;
  const nameRow = wrap.querySelector(
    ".progress-pole-name",
  ) as HTMLElement | null;

  const blocks = Array.from(
    trunk.querySelectorAll(":scope > .progress-trunk-block"),
  ) as HTMLElement[];
  const addRow = trunk.querySelector(
    ":scope > .progress-add-wrap",
  ) as HTMLElement | null;
  const heads: { row: HTMLElement; anchor: BeadAnchor }[] = [];
  for (const block of blocks) {
    const head = block.querySelector(
      ":scope > .progress-row",
    ) as HTMLElement | null;
    if (!head || head.classList.contains("is-grain-hidden")) continue;
    heads.push({ row: head, anchor: beadAnchor(head, origin, scale) });
  }
  if (heads.length === 0 && !addRow && !nameRow && !idRow) return;

  const idAnchor = idRow ? beadAnchor(idRow, origin, scale) : null;
  const nameAnchor = nameRow ? beadAnchor(nameRow, origin, scale) : null;

  const trunkBox = trunk.getBoundingClientRect();
  const trunkSpineX = nameAnchor
    ? nameAnchor.left + NEST_INSET_PX
    : (trunkBox.left - origin.left) / scale + 1;

  if (idAnchor && nameAnchor) {
    paintNestDrop(svg, idAnchor, nameAnchor, mode, cls);
  }

  let yStart: number;
  if (nameAnchor) {
    yStart = mode === "line" ? nameAnchor.midY : nameAnchor.bottom;
  } else if (heads[0]) {
    yStart = heads[0].anchor.midY;
  } else if (addRow) {
    yStart = midY(addRow, origin.top, scale);
  } else {
    return;
  }

  let yEnd = heads.length > 0 ? heads[heads.length - 1].anchor.midY : yStart;
  if (addRow) {
    yEnd = beadAnchor(addRow, origin, scale).midY;
  }

  if (yEnd > yStart) {
    stroke(svg, trunkSpineX, yStart, trunkSpineX, yEnd, cls);
  }

  for (let i = 0; i < heads.length; i++) {
    const { row, anchor } = heads[i];
    paintNode(svg, trunkSpineX, anchor.midY, anchor, mode);
    paintNestUnder(svg, origin, blocks[i], row, anchor, scale, mode, cls);
  }

  if (addRow) {
    const addAnchor = beadAnchor(addRow, origin, scale);
    paintNode(svg, trunkSpineX, addAnchor.midY, addAnchor, mode);
  }
}

function paintNestDrop(
  svg: SVGElement,
  parent: BeadAnchor,
  child: BeadAnchor,
  mode: LinePaintMode,
  cls: string,
): void {
  const nestX = parent.left + NEST_INSET_PX;
  const yJoin = child.midY;
  const yFrom = mode === "line" ? parent.midY : parent.bottom;
  if (yJoin > yFrom) {
    stroke(svg, nestX, yFrom, nestX, yJoin, cls);
  }
  paintNode(svg, nestX, yJoin, child, mode);
}

function paintNestUnder(
  svg: SVGElement,
  origin: DOMRect,
  block: HTMLElement,
  parentRow: HTMLElement,
  parent: BeadAnchor,
  scale: number,
  mode: LinePaintMode,
  cls: string,
): void {
  const parentId = parentRow.dataset.stepId;
  if (!parentId) return;

  const childRows = (
    Array.from(
      block.querySelectorAll(":scope > .progress-depth-row"),
    ) as HTMLElement[]
  ).filter(
    (row) =>
      row.dataset.parentId === parentId &&
      !row.classList.contains("is-grain-hidden"),
  );

  if (childRows.length === 0) return;

  const childAnchors = childRows.map((row) => beadAnchor(row, origin, scale));
  const nestX = parent.left + NEST_INSET_PX;
  const yFirst = childAnchors[0].midY;
  const yLast = childAnchors[childAnchors.length - 1].midY;
  const yFrom = mode === "line" ? parent.midY : parent.bottom;

  if (yFirst > yFrom) {
    stroke(svg, nestX, yFrom, nestX, yFirst, cls);
  }
  if (yLast > yFirst) {
    stroke(svg, nestX, yFirst, nestX, yLast, cls);
  }

  for (let i = 0; i < childRows.length; i++) {
    paintNode(svg, nestX, childAnchors[i].midY, childAnchors[i], mode);
    paintNestUnder(
      svg,
      origin,
      block,
      childRows[i],
      childAnchors[i],
      scale,
      mode,
      cls,
    );
  }
}
