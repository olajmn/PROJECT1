// Column resize with TradingView-style snap to a collapsed width (the
// chat collapses to 0 and is reopened from its show / hide button).
// Used for chat now; same helper can drive the projects sidebar later.
// Hard min while open; edge-trigger collapse/expand so one drag can go both ways.

// Contents
//  1. Types
//      - CollapseRailOpts
//      - CollapseRailApi
//  2. Public API
//      - installCollapseRail()

// 1. Types

export type CollapseRailOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  /** Pane that gets the collapsed class (chat panel, sidebar, …). */
  panel: HTMLElement;
  cssVar: string;
  widthStorageKey: string;
  collapsedStorageKey: string;
  /** Hard floor while open; click opens here too. */
  minWidth: number;
  /** Fraction of container width (e.g. 1/2). Optional. */
  maxFraction?: number;
  /** Leave at least this much for the rest of the container. */
  minOther: number;
  /** Width when collapsed (0 for the chat). */
  railWidth: number;
  /** Falling across this while open → collapse (~ half of min). */
  snapThreshold: number;
  /** Rising across this while collapsed → open (nearer rail than snap). */
  expandThreshold: number;
  containerCollapsedClass: string;
  panelCollapsedClass: string;
  bodyClass: string;
  /** How pointer X maps to column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
};

export type CollapseRailApi = {
  collapse: () => void;
  expand: () => void;
};

// 2. Public API

export function installCollapseRail(opts: CollapseRailOpts): CollapseRailApi {
  let collapsed = localStorage.getItem(opts.collapsedStorageKey) === "1";
  let openWidth = readStoredOpenWidth(opts);
  let dragging = false;
  let activePointerId: number | null = null;
  /** Prior pointer width this drag — edge-trigger snap/expand. */
  let prevRaw: number | null = null;

  const maxOpen = (): number => {
    const byRest = Math.max(
      opts.minWidth,
      opts.container.clientWidth - opts.minOther,
    );
    const byFraction =
      opts.maxFraction != null
        ? opts.container.clientWidth * opts.maxFraction
        : Infinity;
    return Math.min(byFraction, byRest);
  };

  const clampOpen = (px: number): number =>
    Math.min(maxOpen(), Math.max(opts.minWidth, Math.round(px)));

  const setWidth = (px: number): void => {
    opts.container.style.setProperty(opts.cssVar, `${Math.round(px)}px`);
  };

  const pointerWidth = (event: PointerEvent): number =>
    opts.widthFromPointer(
      event.clientX,
      opts.container.getBoundingClientRect(),
    );

  const syncDom = (): void => {
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

  const endDrag = (): void => {
    if (!dragging) return;
    dragging = false;
    prevRaw = null;
    document.body.classList.remove(opts.bodyClass);
    window.removeEventListener("pointerup", onWindowUp);
    window.removeEventListener("pointercancel", onWindowUp);
    window.removeEventListener("blur", onWindowBlur);
    if (activePointerId != null) {
      try {
        opts.handle.releasePointerCapture(activePointerId);
      } catch {
        /* already released */
      }
      activePointerId = null;
    }
  };

  /** Persist from final width, then clear drag (idempotent).
   *  Collapse/expand flip only via edge-trigger mid-drag. Release must
   *  not undo either just because the pointer still sits on the wrong
   *  side of a threshold — once flipped, that state sticks. */
  const finishDrag = (raw: number | null): void => {
    if (!dragging) return;
    const final = raw ?? prevRaw;
    endDrag();
    if (final == null) return;

    if (collapsed) {
      setWidth(opts.railWidth);
      return;
    }
    expand(final);
  };

  const collapse = (): void => {
    collapsed = true;
    localStorage.setItem(opts.collapsedStorageKey, "1");
    setWidth(opts.railWidth);
    syncDom();
  };

  const expand = (width?: number): void => {
    collapsed = false;
    localStorage.setItem(opts.collapsedStorageKey, "0");
    openWidth = clampOpen(width ?? opts.minWidth);
    localStorage.setItem(opts.widthStorageKey, String(openWidth));
    syncDom();
    setWidth(openWidth);
  };

  if (collapsed) setWidth(opts.railWidth);
  else {
    openWidth = clampOpen(openWidth);
    setWidth(openWidth);
  }
  syncDom();

  const onMove = (event: PointerEvent): void => {
    if (!dragging) return;
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    const raw = pointerWidth(event);
    const prev = prevRaw;
    prevRaw = raw;

    if (collapsed) {
      if (roseAcross(prev, raw, opts.expandThreshold) ||
          roseAcross(prev, raw, opts.snapThreshold)) {
        expand(raw);
        return;
      }
      setWidth(opts.railWidth);
      return;
    }

    if (fellAcross(prev, raw, opts.snapThreshold)) {
      collapse();
      return;
    }
    setWidth(clampOpen(raw));
  };

  const onUp = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag(pointerWidth(event));
  };

  const onWindowUp = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag(pointerWidth(event));
  };

  const onWindowBlur = (): void => {
    finishDrag(null);
  };

  const onLostCapture = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    // Capture dropped without a clean pointerup (tab switch, OS gesture, …).
    finishDrag(null);
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    dragging = true;
    activePointerId = event.pointerId;
    prevRaw = pointerWidth(event);
    opts.handle.setPointerCapture(event.pointerId);
    document.body.classList.add(opts.bodyClass);
    window.addEventListener("pointerup", onWindowUp);
    window.addEventListener("pointercancel", onWindowUp);
    window.addEventListener("blur", onWindowBlur);
  });
  opts.handle.addEventListener("pointermove", onMove);
  opts.handle.addEventListener("pointerup", onUp);
  opts.handle.addEventListener("pointercancel", onUp);
  opts.handle.addEventListener("lostpointercapture", onLostCapture);

  window.addEventListener("resize", () => {
    if (collapsed) {
      setWidth(opts.railWidth);
      return;
    }
    openWidth = clampOpen(openWidth);
    setWidth(openWidth);
  });

  return { collapse, expand };
}

function readStoredOpenWidth(opts: CollapseRailOpts): number {
  const stored = Number(localStorage.getItem(opts.widthStorageKey));
  return Number.isFinite(stored) && stored >= opts.minWidth
    ? stored
    : opts.minWidth;
}

/** Pointer rose across `threshold` (prev below, now at/above). */
function roseAcross(
  prev: number | null,
  raw: number,
  threshold: number,
): boolean {
  return prev != null && prev < threshold && raw >= threshold;
}

/** Pointer fell across `threshold` (prev at/above, now below). */
function fellAcross(
  prev: number | null,
  raw: number,
  threshold: number,
): boolean {
  return prev != null && prev >= threshold && raw < threshold;
}
