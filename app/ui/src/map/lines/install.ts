/**
 * Install / refresh the SVG nest overlay on a `.progress-line` wrap.
 */

import { isSkeletonMap } from "../skeleton/mode.js";
import { paintMapNest } from "./paint.js";
import { measureMapContent, svgEl } from "./svg.js";

type LinesHost = HTMLElement & {
  _mapLinesRo?: ResizeObserver;
  _mapLinesPaint?: () => void;
};

function paintOnce(wrap: LinesHost, svg: SVGSVGElement): void {
  void wrap.offsetWidth;

  const { w, h } = measureMapContent(wrap);
  svg.setAttribute("width", String(w));
  svg.setAttribute("height", String(h));
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const mode = isSkeletonMap(wrap) ? "line" : "text";
  paintMapNest(wrap, svg, mode);
}

/** Schedule a paint after layout — double rAF covers mode/grain settle. */
export function scheduleMapLines(wrap: HTMLElement): void {
  const host = wrap as LinesHost;
  const paint = host._mapLinesPaint;
  if (!paint) {
    installMapLines(wrap);
    return;
  }
  requestAnimationFrame(() => {
    paint();
    requestAnimationFrame(paint);
  });
}

/**
 * Paint / refresh an SVG overlay on a .progress-line wrap.
 */
export function installMapLines(wrap: HTMLElement): void {
  const host = wrap as LinesHost;
  let svg = wrap.querySelector(
    ":scope > .progress-map-svg",
  ) as SVGSVGElement | null;
  if (!svg) {
    svg = svgEl("svg", { class: "progress-map-svg" }) as SVGSVGElement;
    wrap.insertBefore(svg, wrap.firstChild);
  }

  const paint = (): void => {
    paintOnce(host, svg!);
  };
  host._mapLinesPaint = paint;

  paint();
  requestAnimationFrame(() => {
    paint();
    requestAnimationFrame(paint);
  });

  if (!host._mapLinesRo) {
    const ro = new ResizeObserver(() => scheduleMapLines(wrap));
    ro.observe(wrap);
    host._mapLinesRo = ro;
  }
}
