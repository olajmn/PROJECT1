/**
 * SVG connectors for the live project map.
 * Identity (#40) → name (project-1) → trunk (Authorities…).
 * One continuous join at shared coordinates.
 */

const NS = "http://www.w3.org/2000/svg";
const DROP_GAP = 11; // px — verticals start under the parent label
const LABEL_GAP = 8; // px — horizontals stop short of the letters

const NEST_INSET = 16; // px — nest spine steps right of the parent tick end

function tickEnd(xLabel: number, spineX: number): number {
  return Math.max(spineX, xLabel - LABEL_GAP);
}

function svgEl(
  name: string,
  attrs: Record<string, string | number>,
): SVGElement {
  const el = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) {
    el.setAttribute(k, String(v));
  }
  return el;
}

function stroke(
  svg: SVGElement,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): void {
  svg.appendChild(
    svgEl("line", {
      x1,
      y1,
      x2,
      y2,
      class: "progress-svg-stroke",
      "stroke-linecap": "square",
    }),
  );
}

function midY(el: HTMLElement, originTop: number): number {
  const r = el.getBoundingClientRect();
  return r.top - originTop + r.height / 2;
}

function leftX(el: HTMLElement, originLeft: number): number {
  return el.getBoundingClientRect().left - originLeft;
}

function labelOf(row: HTMLElement): HTMLElement {
  return (
    (row.querySelector(
      ".progress-bead-btn, .progress-bead-label",
    ) as HTMLElement | null) ?? row
  );
}

/**
 * Paint / refresh an SVG overlay on a .progress-line wrap.
 */
export function installMapSvg(wrap: HTMLElement): void {
  let svg = wrap.querySelector(":scope > .progress-map-svg") as SVGSVGElement | null;
  if (!svg) {
    svg = svgEl("svg", { class: "progress-map-svg" }) as SVGSVGElement;
    wrap.insertBefore(svg, wrap.firstChild);
  }

  const redraw = (): void => {
    const w = Math.max(wrap.clientWidth, 1);
    const h = Math.max(wrap.scrollHeight, 1);
    svg!.setAttribute("width", String(w));
    svg!.setAttribute("height", String(h));
    svg!.setAttribute("viewBox", `0 0 ${w} ${h}`);
    while (svg!.firstChild) svg!.removeChild(svg!.firstChild);

    const origin = wrap.getBoundingClientRect();
    const trunk = wrap.querySelector(".progress-trunk") as HTMLElement | null;
    if (!trunk) return;

    const idRow = wrap.querySelector(
      ".progress-pole-identity",
    ) as HTMLElement | null;
    const nameRow = wrap.querySelector(
      ".progress-pole-name, .progress-pole-root",
    ) as HTMLElement | null;

    const trunkBox = trunk.getBoundingClientRect();
    // Trunk spine sits under the name (children grow from project-1).
    const trunkSpineX = trunkBox.left - origin.left + 1;

    const blocks = Array.from(
      trunk.querySelectorAll(":scope > .progress-trunk-block"),
    ) as HTMLElement[];
    const addRow = trunk.querySelector(
      ":scope > .progress-add-wrap",
    ) as HTMLElement | null;

    const heads: { row: HTMLElement; y: number; xLabel: number }[] = [];
    for (const block of blocks) {
      const head = block.querySelector(
        ":scope > .progress-row",
      ) as HTMLElement | null;
      if (!head) continue;
      const lab = labelOf(head);
      heads.push({
        row: head,
        y: midY(head, origin.top),
        xLabel: leftX(lab, origin.left),
      });
    }
    if (heads.length === 0 && !addRow && !nameRow) return;

    // --- Identity → name (#40 → project-1) ---
    if (idRow && nameRow) {
      const idLabel =
        (idRow.querySelector(".entity-id") as HTMLElement | null) ?? idRow;
      const nameLabel =
        (nameRow.querySelector("span:not(.progress-branch)") as HTMLElement | null) ??
        nameRow;
      const idX = leftX(idLabel, origin.left) + 4;
      const yId = midY(idRow, origin.top);
      const yName = midY(nameRow, origin.top);
      const xName = leftX(nameLabel, origin.left) - LABEL_GAP;

      // Drop starts under #40, ends at project-1 mid for the elbow.
      stroke(svg!, idX, yId + DROP_GAP, idX, yName);
      stroke(svg!, idX, yName, Math.max(idX, xName), yName);
    }

    // --- Name → trunk (Authorities… grow from project-1) ---
    let yStart = heads[0]?.y ?? (addRow ? midY(addRow, origin.top) : 0);
    if (nameRow) {
      yStart = midY(nameRow, origin.top) + DROP_GAP;
    }
    let yEnd = heads.length > 0 ? heads[heads.length - 1].y : yStart;
    if (addRow) {
      yEnd = midY(addRow, origin.top);
    }

    if (yEnd > yStart) {
      stroke(svg!, trunkSpineX, yStart, trunkSpineX, yEnd);
    }

    // Bridge from name over to trunk spine (at label mid); vertical already
    // starts below the word.
    if (nameRow) {
      const nameLabel =
        (nameRow.querySelector("span:not(.progress-branch)") as HTMLElement | null) ??
        nameRow;
      const xName = leftX(nameLabel, origin.left) - LABEL_GAP;
      const yName = midY(nameRow, origin.top);
      if (Math.abs(xName - trunkSpineX) > 2) {
        stroke(
          svg!,
          Math.min(xName, trunkSpineX),
          yName,
          Math.max(xName, trunkSpineX),
          yName,
        );
      }
    }

    for (let i = 0; i < heads.length; i++) {
      const { y, xLabel } = heads[i];
      const xTick = tickEnd(xLabel, trunkSpineX);
      stroke(svg!, trunkSpineX, y, xTick, y);

      paintNestUnder(svg!, origin, blocks[i], heads[i].row, y, xTick, trunkSpineX);
    }

    if (addRow) {
      const yAdd = midY(addRow, origin.top);
      stroke(svg!, trunkSpineX, yAdd, trunkSpineX + 14, yAdd);
    }
  };

  const schedule = (): void => {
    requestAnimationFrame(redraw);
  };
  schedule();
  window.setTimeout(schedule, 40);

  const tagged = wrap as HTMLElement & { _mapSvgRo?: ResizeObserver };
  if (!tagged._mapSvgRo) {
    const ro = new ResizeObserver(schedule);
    ro.observe(wrap);
    tagged._mapSvgRo = ro;
  }
}

/**
 * Draw nest spines for every generation under `parentRow`.
 * Rows are flat in the trunk block; parentId links each generation.
 */
function paintNestUnder(
  svg: SVGElement,
  origin: DOMRect,
  block: HTMLElement,
  parentRow: HTMLElement,
  parentY: number,
  parentTickEndX: number,
  mainSpineX: number,
): void {
  const parentId = parentRow.dataset.stepId;
  if (!parentId) return;

  const childRows = (
    Array.from(
      block.querySelectorAll(":scope > .progress-depth-row"),
    ) as HTMLElement[]
  ).filter((row) => row.dataset.parentId === parentId);

  if (childRows.length === 0) return;

  const nestX = parentTickEndX + NEST_INSET;
  const childYs = childRows.map((row) => midY(row, origin.top));
  const yFirst = childYs[0];
  const yLast = childYs[childYs.length - 1];
  const yDrop = parentY + DROP_GAP;

  // Vertical starts under the parent word, not through it.
  stroke(svg, nestX, yDrop, nestX, yFirst);
  if (yLast > yFirst) {
    stroke(svg, nestX, yFirst, nestX, yLast);
  }

  // Parent tick only — no vertical through the letters.
  if (nestX > mainSpineX + 2) {
    stroke(svg, parentTickEndX, parentY, nestX, parentY);
  }

  for (let i = 0; i < childRows.length; i++) {
    const lab = labelOf(childRows[i]);
    const xLabel = leftX(lab, origin.left);
    const xEnd = tickEnd(xLabel, nestX);
    stroke(svg, nestX, childYs[i], xEnd, childYs[i]);
    // Recurse: children of children get their own stepped spine.
    paintNestUnder(
      svg,
      origin,
      block,
      childRows[i],
      childYs[i],
      xEnd,
      mainSpineX,
    );
  }
}
