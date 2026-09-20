// Column resize with TradingView-style snap to a narrow icon rail.
// Used for chat now; same helper can drive the projects sidebar later.

// Contents
//  1. Options
//      - CollapseRailOpts
//  2. Public API
//      - CollapseRailApi
//      - installCollapseRail()

// 1. Options

export type CollapseRailOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  /** Pane that gets the collapsed class (chat panel, sidebar, …). */
  panel: HTMLElement;
  cssVar: string;
  widthStorageKey: string;
  collapsedStorageKey: string;
  defaultWidth: number;
  minWidth: number;
  maxWidthCap: number;
  /** Leave at least this much for the rest of the container. */
  minOther: number;
  /** Width when snapped to the icon rail. */
  railWidth: number;
  /** On pointer-up below this (while open), snap to the rail. */
  snapThreshold: number;
  /**
   * While dragging below this width, `--column-rail-progress` ramps 0→1
   * toward snapThreshold so the pane can preview collapse. Defaults to minWidth.
   */
  warnStart?: number;
  /** Class on panel while collapse-progress > 0 during an open drag. */
  pendingClass?: string;
  containerCollapsedClass: string;
  panelCollapsedClass: string;
  bodyClass: string;
  /** How pointer X maps to the column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
};

// 2. Public API

export type CollapseRailApi = {
  collapse: () => void;
  expand: () => void;
  isCollapsed: () => boolean;
};

export function installCollapseRail(opts: CollapseRailOpts): CollapseRailApi {
  const pendingClass = opts.pendingClass ?? "is-collapse-pending";
  const warnStart = opts.warnStart ?? opts.minWidth;

  let collapsed = localStorage.getItem(opts.collapsedStorageKey) === "1";
  let openWidth = (() => {
    const stored = Number(localStorage.getItem(opts.widthStorageKey));
    return Number.isFinite(stored) && stored >= opts.minWidth
      ? stored
      : opts.defaultWidth;
  })();

  const maxOpen = () =>
    Math.min(
      opts.maxWidthCap,
      Math.max(opts.minWidth, opts.container.clientWidth - opts.minOther),
    );

  const clampOpen = (px: number) =>
    Math.min(maxOpen(), Math.max(opts.minWidth, Math.round(px)));

  const setWidth = (px: number) => {
    opts.container.style.setProperty(opts.cssVar, `${Math.round(px)}px`);
  };

  const setCollapseProgress = (raw: number) => {
    const span = warnStart - opts.snapThreshold;
    let t = 0;
    if (span > 0) {
      if (raw <= opts.snapThreshold) t = 1;
      else if (raw < warnStart) t = (warnStart - raw) / span;
    }
    t = Math.min(1, Math.max(0, t));
    opts.panel.style.setProperty("--column-rail-progress", t.toFixed(3));
    opts.panel.classList.toggle(pendingClass, t > 0);
  };

  const clearCollapseProgress = () => {
    opts.panel.style.removeProperty("--column-rail-progress");
    opts.panel.classList.remove(pendingClass);
  };

  const syncDom = () => {
    opts.container.classList.toggle(opts.containerCollapsedClass, collapsed);
    opts.panel.classList.toggle(opts.panelCollapsedClass, collapsed);
    opts.handle.setAttribute(
      "aria-label",
      collapsed ? "Expand column" : "Resize column",
    );
    opts.handle.title = collapsed
      ? "Drag to expand column"
      : "Drag to resize column";
  };

  const collapse = () => {
    collapsed = true;
    localStorage.setItem(opts.collapsedStorageKey, "1");
    clearCollapseProgress();
    setWidth(opts.railWidth);
    syncDom();
  };

  const expand = (width?: number) => {
    collapsed = false;
    localStorage.setItem(opts.collapsedStorageKey, "0");
    openWidth = clampOpen(width ?? openWidth);
    localStorage.setItem(opts.widthStorageKey, String(openWidth));
    clearCollapseProgress();
    setWidth(openWidth);
    syncDom();
  };

  const isCollapsed = () => collapsed;

  if (collapsed) {
    setWidth(opts.railWidth);
  } else {
    openWidth = clampOpen(openWidth);
    setWidth(openWidth);
  }
  syncDom();

  let dragging = false;

  const onMove = (event: PointerEvent) => {
    if (!dragging) return;
    const raw = opts.widthFromPointer(
      event.clientX,
      opts.container.getBoundingClientRect(),
    );
    if (collapsed) {
      clearCollapseProgress();
      if (raw >= opts.snapThreshold) {
        setWidth(clampOpen(raw));
      } else {
        setWidth(opts.railWidth);
      }
      return;
    }
    const preview = Math.min(
      maxOpen(),
      Math.max(opts.railWidth, Math.round(raw)),
    );
    setWidth(preview);
    setCollapseProgress(raw);
  };

  const onUp = (event: PointerEvent) => {
    if (!dragging) return;
    dragging = false;
    opts.handle.releasePointerCapture(event.pointerId);
    document.body.classList.remove(opts.bodyClass);

    const raw = opts.widthFromPointer(
      event.clientX,
      opts.container.getBoundingClientRect(),
    );
    if (collapsed) {
      clearCollapseProgress();
      if (raw >= opts.snapThreshold) {
        expand(raw);
      } else {
        setWidth(opts.railWidth);
        syncDom();
      }
      return;
    }

    if (raw < opts.snapThreshold) {
      collapse();
      return;
    }
    expand(raw);
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    dragging = true;
    opts.handle.setPointerCapture(event.pointerId);
    document.body.classList.add(opts.bodyClass);
  });
  opts.handle.addEventListener("pointermove", onMove);
  opts.handle.addEventListener("pointerup", onUp);
  opts.handle.addEventListener("pointercancel", onUp);

  window.addEventListener("resize", () => {
    if (collapsed) {
      setWidth(opts.railWidth);
      return;
    }
    openWidth = clampOpen(openWidth);
    setWidth(openWidth);
  });

  return { collapse, expand, isCollapsed };
}
