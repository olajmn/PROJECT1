/**
 * Shared SVG helpers for map nest strokes.
 */

const NS = "http://www.w3.org/2000/svg";

export type BeadAnchor = {
  left: number;
  midY: number;
  bottom: number;
  width: number;
};

export function svgEl(
  name: string,
  attrs: Record<string, string | number>,
): SVGElement {
  const el = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) {
    el.setAttribute(k, String(v));
  }
  return el;
}

export function wrapScale(wrap: HTMLElement): number {
  const raw = Number(wrap.dataset.mapScale || "1");
  return Number.isFinite(raw) && raw > 0 ? raw : 1;
}

export function midY(
  el: HTMLElement,
  originTop: number,
  scale: number,
): number {
  const r = el.getBoundingClientRect();
  return (r.top - originTop + r.height / 2) / scale;
}

/** Anchor for a bead / header / add control on a row. */
export function beadAnchor(
  row: HTMLElement,
  origin: DOMRect,
  scale: number,
): BeadAnchor {
  const unit = row.querySelector(
    ".progress-bead-unit, .progress-add, .progress-header-unit",
  ) as HTMLElement | null;
  const el = unit ?? row;
  const r = el.getBoundingClientRect();
  return {
    left: (r.left - origin.left) / scale,
    midY: (r.top - origin.top + r.height / 2) / scale,
    bottom: (r.bottom - origin.top) / scale,
    width: r.width / scale,
  };
}

export function stroke(
  svg: SVGElement,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  className = "progress-svg-stroke",
): void {
  svg.appendChild(
    svgEl("line", {
      x1,
      y1,
      x2,
      y2,
      class: className,
      "stroke-linecap": "square",
    }),
  );
}

/**
 * Natural content size of the map wrap — excludes the absolute SVG
 * overlay (its width/height attributes must not inflate scroll metrics).
 * Width is the spine’s own size, not the frame’s clientWidth.
 */
export function measureMapContent(wrap: HTMLElement): { w: number; h: number } {
  const svg = wrap.querySelector(
    ":scope > .progress-map-svg",
  ) as HTMLElement | null;
  const prevDisplay = svg?.style.display;
  if (svg) svg.style.display = "none";

  const spine = wrap.querySelector(".progress-spine") as HTMLElement | null;
  const box = spine ?? wrap;
  const w = Math.max(box.offsetWidth, box.scrollWidth, 1);
  const h = Math.max(box.offsetHeight, box.scrollHeight, 1);

  if (svg) svg.style.display = prevDisplay ?? "";
  return { w, h };
}

/** Empty project: `#N` / title / hint, no waypoints yet. */
export function isEmptyMap(wrap: HTMLElement): boolean {
  return Boolean(wrap.querySelector(".progress-empty-gap"));
}
