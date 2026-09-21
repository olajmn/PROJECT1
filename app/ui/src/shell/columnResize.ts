// Projects shell column widths — sidebar | map | chat.
//
// Contents
//  1. Three-column rules (edit here)
//  2. Shared column resize
//      - installColumnResize()
//  3. Installers
//      - installSidebarResize()
//      - installChatResize()

import {
  installCollapseRail,
  type CollapseRailApi,
} from "./columnRail/collapseRail.js";

// 1. Three-column rules (edit here)
//
//   ┌──────────┬─────────────────┬──────────┐
//   │ sidebar  │ map (flexible)  │   chat   │
//   └──────────┴─────────────────┴──────────┘
//
// Map has no own width var — it takes leftover space.
// maxFraction is of that column's container (shell for sidebar,
// workspace for chat).

const MAP = {
  /** Soft floor so the middle pane stays usable. */
  minPx: 280,
};

const SIDEBAR = {
  storageKey: "projects.sidebarWidthPx",
  cssVar: "--sidebar-width",
  defaultPx: 240,
  minPx: 180,
  /** Of .app-shell — 1/2 ≈ drag out to mid-screen. */
  maxFraction: 1 / 2,
  /** Leave at least this much for map + chat together. */
  minRestPx: MAP.minPx + 240,
  bodyClass: "is-resizing-sidebar",
};

const CHAT = {
  widthStorageKey: "projects.chatWidthPx",
  collapsedStorageKey: "projects.chatCollapsed",
  cssVar: "--chat-width",
  /** Hard min while open; click opens here. Snap = half of this. */
  minPx: 320,
  /** Of .workspace — same three-way feel as sidebar. */
  maxFraction: 1 / 2,
  /** Leave at least this much for the map. */
  minOtherPx: MAP.minPx,
  /** Collapsed strip — keep in sync with css/shell/columnRail.css */
  railWidthPx: 64,
  /** Rising across this while collapsed → open (nearer rail than snap). */
  expandThresholdPx: 100,
  bodyClass: "is-resizing-chat",
  containerCollapsedClass: "is-chat-collapsed",
  panelCollapsedClass: "is-collapsed",
};

// 2. Shared column resize

type ColumnResizeOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  cssVar: string;
  storageKey: string;
  defaultWidth: number;
  minWidth: number;
  /** Absolute ceiling (optional; prefer maxFraction). */
  maxWidthCap?: number;
  /** Fraction of container width (e.g. 1/2). */
  maxFraction?: number;
  /** Leave at least this much for the rest of the container. */
  minOther: number;
  /** How pointer X maps to the column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
  bodyClass: string;
};

function maxAllowed(
  container: HTMLElement,
  minWidth: number,
  minOther: number,
  maxFraction?: number,
  maxWidthCap?: number,
): number {
  const byRest = Math.max(minWidth, container.clientWidth - minOther);
  const byFraction =
    maxFraction != null ? container.clientWidth * maxFraction : Infinity;
  const byCap = maxWidthCap ?? Infinity;
  return Math.min(byRest, byFraction, byCap);
}

function installColumnResize(opts: ColumnResizeOpts): void {
  const apply = (px: number) => {
    const max = maxAllowed(
      opts.container,
      opts.minWidth,
      opts.minOther,
      opts.maxFraction,
      opts.maxWidthCap,
    );
    const clamped = Math.min(max, Math.max(opts.minWidth, Math.round(px)));
    opts.container.style.setProperty(opts.cssVar, `${clamped}px`);
    return clamped;
  };

  const stored = Number(localStorage.getItem(opts.storageKey));
  apply(Number.isFinite(stored) && stored > 0 ? stored : opts.defaultWidth);

  let dragging = false;
  let activePointerId: number | null = null;

  const persist = (): void => {
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) {
      localStorage.setItem(opts.storageKey, String(Math.round(px)));
    }
  };

  const endDrag = (): void => {
    if (!dragging) return;
    dragging = false;
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

  const finishDrag = (): void => {
    if (!dragging) return;
    endDrag();
    persist();
  };

  const onMove = (event: PointerEvent) => {
    if (!dragging) return;
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    apply(
      opts.widthFromPointer(event.clientX, opts.container.getBoundingClientRect()),
    );
  };

  const onUp = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  const onWindowUp = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  const onWindowBlur = (): void => {
    finishDrag();
  };

  const onLostCapture = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    dragging = true;
    activePointerId = event.pointerId;
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
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) apply(px);
  });
}

// 3. Installers

export function installSidebarResize(
  shell: HTMLElement,
  handle: HTMLElement,
): void {
  installColumnResize({
    container: shell,
    handle,
    cssVar: SIDEBAR.cssVar,
    storageKey: SIDEBAR.storageKey,
    defaultWidth: SIDEBAR.defaultPx,
    minWidth: SIDEBAR.minPx,
    maxFraction: SIDEBAR.maxFraction,
    minOther: SIDEBAR.minRestPx,
    widthFromPointer: (clientX, rect) => clientX - rect.left,
    bodyClass: SIDEBAR.bodyClass,
  });
}

export function installChatResize(
  workspace: HTMLElement,
  handle: HTMLElement,
  panel: HTMLElement,
): CollapseRailApi {
  return installCollapseRail({
    container: workspace,
    handle,
    panel,
    cssVar: CHAT.cssVar,
    widthStorageKey: CHAT.widthStorageKey,
    collapsedStorageKey: CHAT.collapsedStorageKey,
    minWidth: CHAT.minPx,
    maxFraction: CHAT.maxFraction,
    minOther: CHAT.minOtherPx,
    railWidth: CHAT.railWidthPx,
    snapThreshold: Math.round(CHAT.minPx / 2),
    expandThreshold: CHAT.expandThresholdPx,
    containerCollapsedClass: CHAT.containerCollapsedClass,
    panelCollapsedClass: CHAT.panelCollapsedClass,
    bodyClass: CHAT.bodyClass,
    widthFromPointer: (clientX, rect) => rect.right - clientX,
  });
}
