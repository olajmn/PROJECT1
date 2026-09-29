/**
 * Pan + zoom camera inside `.map-frame`.
 * Wheel pans; pinch / Ctrl+wheel zooms, anchored under the cursor
 * vertically; spine stays left-locked.
 * Pan is clamped so a top gap above the tree is not possible.
 * Closest in = 1× (natural bead size). Overview fit is where a reset
 * lands, not a wall — zoom may pull back past it, so it never sits
 * dead on a tree that already fits the frame.
 */

/*
 * Contents
 *
 * 1. Constants and Types
 *
 * 2. Geometry and Layout Helpers
 *    - frameInner()
 *    - overviewFloor()
 *    - zoomFloor()
 *    - pointerInFrame()
 *    - clampPan()
 *    - layoutSlotForCamera()
 *
 * 3. Paint and Apply
 *    - placeStage()
 *    - paintFrame()
 *    - apply()
 *    - applyPanOnly()
 *    - reapplySoft()
 *    - fitOverview()
 *    - zoomAt()
 *
 * 4. Interaction Handlers
 *    - isInteractive()
 *    - onWheel()
 *    - onPointerDown()
 *    - onPointerMove()
 *    - onPointerUp()
 *    - onDblClick()
 *
 * 5. Event Wiring and Public Handle
 *
 * 6. Utilities
 *    - clamp()
 */

import { installMapLines } from "../lines/addLines.js";
import { isEmptyMap } from "../lines/svgHelpers.js";
import {
  clearMapViewPin,
  setMapView,
  syncSkeletonFromZoom,
} from "../lineView/textOrLine.js";

// 1. Constants and Types

const ABS_MIN_ZOOM = 0.08;
const MAX_ZOOM = 1;
/** Most zoom one wheel event may apply. */
const WHEEL_STEP = 1.12;
/** Pinch / Ctrl+wheel zoom sensitivity, per pixel of `deltaY`. */
const ZOOM_PER_PX = 0.01;
/** Pixels per line when a wheel reports `deltaMode` in lines. */
const LINE_PX = 16;
/** Quiet time after the last wheel-pan before the full repaint. */
const WHEEL_SETTLE_MS = 120;
const LEFT_PAD = 8;
/** How far past the overview fit zoom may still pull back. */
const OUT_PAST_FIT = 0.4;

/** Zoom and vertical pan — what a re-render must carry over. */
export type CameraPose = { zoom: number; panY: number };

export type MapCameraHandle = {
  getPose: () => CameraPose;
  setPose: (pose: CameraPose) => void;
  setEnabled: (on: boolean) => void;
  setContentSize: (w: number, h: number) => void;
  resetOverview: () => void;
  isDirty: () => boolean;
  markDirty: () => void;
  nudgePan: (dy: number) => void;
  panToTop: () => void;
  reapply: () => void;
  destroy: () => void;
};

type CameraOpts = {
  onChange?: () => void;
};

export function installMapCamera(
  viewport: HTMLElement,
  slot: HTMLElement,
  stage: HTMLElement,
  mapEl: HTMLElement,
  opts: CameraOpts = {},
): MapCameraHandle {
  let enabled = false;
  let contentW = 1;
  let contentH = 1;
  let zoom = 1;
  let panX = 0;
  let panY = 0;
  let dirty = false;
  let dragging = false;
  let lastY = 0;
  let wheelSettle: ReturnType<typeof setTimeout> | undefined;

  // 2. Geometry and Layout Helpers

  const frameInner = (): { w: number; h: number; pl: number; pt: number } => {
    const cs = getComputedStyle(viewport);
    const pl = parseFloat(cs.paddingLeft) || 0;
    const pr = parseFloat(cs.paddingRight) || 0;
    const pt = parseFloat(cs.paddingTop) || 0;
    const pb = parseFloat(cs.paddingBottom) || 0;
    return {
      w: Math.max(viewport.clientWidth - pl - pr, 1),
      h: Math.max(viewport.clientHeight - pt - pb, 1),
      pl,
      pt,
    };
  };

  /** Furthest out — whole tree still fits (capped at 1). */
  const overviewFloor = (): number => {
    const { w, h } = frameInner();
    return clamp(Math.min(1, w / contentW, h / contentH), ABS_MIN_ZOOM, 1);
  };

  /**
   * Zoom-out limit, deliberately below the overview fit. On a tree that
   * already fits, fit == 1× == max, so a fit-as-wall leaves zoom
   * completely dead in both directions, which reads as broken.
   * `fitOverview()` still lands on `overviewFloor()`.
   */
  const zoomFloor = (): number =>
    clamp(overviewFloor() * OUT_PAST_FIT, ABS_MIN_ZOOM, MAX_ZOOM);

  const pointerInFrame = (
    clientX: number,
    clientY: number,
  ): { x: number; y: number } => {
    const vr = viewport.getBoundingClientRect();
    const { pl, pt } = frameInner();
    return { x: clientX - vr.left - pl, y: clientY - vr.top - pt };
  };

  const clampPan = (): void => {
    panX = LEFT_PAD;
    const { h } = frameInner();
    const maxY = LEFT_PAD;
    const minY = Math.min(maxY, h - contentH * zoom - LEFT_PAD);
    panY = clamp(panY, minY, maxY);
  };

  const layoutSlotForCamera = (): void => {
    slot.style.width = "100%";
    slot.style.height = "100%";
    slot.style.overflow = "visible";
    stage.style.position = "absolute";
    stage.style.left = "0";
    stage.style.top = "0";
    stage.style.width = `${contentW}px`;
    stage.style.height = `${contentH}px`;
  };

  // 3. Paint and Apply

  /** Move `stage` to the current pan/zoom, and hand the same numbers to
   *  CSS so the dot grid behind the map (css/panes/canvas/dotGrid.css)
   *  moves with it. */
  const placeStage = (): void => {
    stage.style.transformOrigin = "0 0";
    stage.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    viewport.style.setProperty("--cam-x", `${panX}px`);
    viewport.style.setProperty("--cam-y", `${panY}px`);
    viewport.style.setProperty("--cam-zoom", String(zoom));
  };

  /** Paint the current zoom/pan onto `stage` and rebuild the line nest. */
  const paintFrame = (): void => {
    mapEl.dataset.mapScale = String(zoom);
    syncSkeletonFromZoom(mapEl, zoom);
    placeStage();
    installMapLines(mapEl);
    opts.onChange?.();
  };

  const apply = (): void => {
    if (!enabled) return;
    zoom = clamp(zoom, zoomFloor(), MAX_ZOOM);
    clampPan();
    paintFrame();
  };

  /**
   * Pan-only reposition during an active drag — moves `stage` as a rigid
   * body (translate only, zoom unchanged) so the SVG nest inside it stays
   * aligned without a repaint. Skips `installMapLines()`, which tears down
   * and rebuilds the whole overlay; that full rebuild runs once on
   * pointerup instead, via `apply()`.
   */
  const applyPanOnly = (): void => {
    if (!enabled) return;
    clampPan();
    placeStage();
    opts.onChange?.();
  };

  /** Grain keep: raise zoom if below floor; do not pull down to overview. */
  const reapplySoft = (): void => {
    if (!enabled) return;
    layoutSlotForCamera();
    const floor = zoomFloor();
    if (zoom < floor) zoom = floor;
    if (zoom > MAX_ZOOM) zoom = MAX_ZOOM;
    clampPan();
    paintFrame();
  };

  const fitOverview = (): void => {
    // Empty landing: always natural size (1×) + Text — not a hairline fit.
    zoom = isEmptyMap(mapEl) ? MAX_ZOOM : overviewFloor();
    panX = LEFT_PAD;
    panY = LEFT_PAD;
    dirty = false;
    clearMapViewPin(mapEl);
    if (isEmptyMap(mapEl)) setMapView(mapEl, "text");
    apply();
  };

  const zoomAt = (factor: number, fy: number): void => {
    const oldZ = zoom;
    const newZ = clamp(oldZ * factor, zoomFloor(), MAX_ZOOM);
    if (newZ === oldZ) return;
    const cy = (fy - panY) / oldZ;
    zoom = newZ;
    panX = LEFT_PAD;
    panY = fy - cy * newZ;
    dirty = true;
    apply();
  };

  // 4. Interaction Handlers

  const isInteractive = (target: EventTarget | null): boolean => {
    if (!(target instanceof Element)) return false;
    return Boolean(
      target.closest(
        "button, a, input, textarea, select, label, .progress-menu, .progress-bead-btn, .progress-add, .progress-name-label, .progress-name-input, .map-top-bar",
      ),
    );
  };

  /**
   * Plain wheel / two-finger scroll pans; Ctrl/Cmd+wheel zooms. A trackpad
   * pinch arrives as a Ctrl+wheel event, so pinch zooms with no extra
   * code. Zoom follows the size of `deltaY` (a trackpad sends many tiny
   * events, a mouse notch one large one), capped at `WHEEL_STEP` per event
   * so one mouse notch stays a single modest step.
   */
  const onWheel = (event: WheelEvent): void => {
    if (!enabled) return;
    event.preventDefault();
    const dy =
      event.deltaMode === WheelEvent.DOM_DELTA_LINE
        ? event.deltaY * LINE_PX
        : event.deltaY;
    if (event.ctrlKey || event.metaKey) {
      const factor = clamp(
        Math.exp(-dy * ZOOM_PER_PX),
        1 / WHEEL_STEP,
        WHEEL_STEP,
      );
      zoomAt(factor, pointerInFrame(event.clientX, event.clientY).y);
      return;
    }
    panY -= dy;
    panX = LEFT_PAD;
    dirty = true;
    applyPanOnly();
    // No "scroll ended" event exists; rebuild the line nest once the
    // scroll goes quiet, as onPointerUp() does after a drag.
    if (wheelSettle !== undefined) clearTimeout(wheelSettle);
    wheelSettle = setTimeout(() => {
      wheelSettle = undefined;
      apply();
    }, WHEEL_SETTLE_MS);
  };

  const onPointerDown = (event: PointerEvent): void => {
    if (!enabled) return;
    if (event.button !== 0) return;
    if (isInteractive(event.target)) return;
    dragging = true;
    lastY = event.clientY;
    viewport.classList.add("is-panning");
    viewport.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: PointerEvent): void => {
    if (!enabled || !dragging) return;
    panY += event.clientY - lastY;
    lastY = event.clientY;
    panX = LEFT_PAD;
    dirty = true;
    applyPanOnly();
  };

  const onPointerUp = (event: PointerEvent): void => {
    if (!dragging) return;
    dragging = false;
    viewport.classList.remove("is-panning");
    try {
      viewport.releasePointerCapture(event.pointerId);
    } catch {
      /* already released */
    }
    apply();
  };

  const onDblClick = (event: MouseEvent): void => {
    if (!enabled) return;
    if (isInteractive(event.target)) return;
    event.preventDefault();
    fitOverview();
  };

  // 5. Event Wiring and Public Handle

  viewport.addEventListener("wheel", onWheel, { passive: false });
  viewport.addEventListener("pointerdown", onPointerDown);
  viewport.addEventListener("pointermove", onPointerMove);
  viewport.addEventListener("pointerup", onPointerUp);
  viewport.addEventListener("pointercancel", onPointerUp);
  viewport.addEventListener("dblclick", onDblClick);

  return {
    getPose: () => ({ zoom, panY }),

    /** Restore a pose from before a re-render, without painting: it
     *  counts as the user's own view (dirty), so the next paint keeps it
     *  instead of fitting the overview. */
    setPose: (pose: CameraPose) => {
      zoom = pose.zoom;
      panY = pose.panY;
      dirty = true;
    },

    setEnabled: (on: boolean) => {
      enabled = on;
      viewport.classList.toggle("is-camera-on", on);
      if (!on) {
        dragging = false;
        viewport.classList.remove("is-panning");
        setMapView(mapEl, "text");
        clearMapViewPin(mapEl);
        slot.style.overflow = "hidden";
        stage.style.position = "absolute";
        stage.style.left = "0";
        stage.style.top = "0";
        stage.style.transform = "none";
        for (const name of ["--cam-x", "--cam-y", "--cam-zoom"]) {
          viewport.style.removeProperty(name);
        }
        mapEl.dataset.mapScale = "1";
        dirty = false;
      } else {
        layoutSlotForCamera();
      }
    },

    setContentSize: (w: number, h: number) => {
      contentW = Math.max(w, 1);
      contentH = Math.max(h, 1);
      if (enabled) layoutSlotForCamera();
    },

    resetOverview: () => {
      if (!enabled) return;
      layoutSlotForCamera();
      fitOverview();
    },

    isDirty: () => dirty,

    markDirty: () => {
      dirty = true;
    },

    /**
     * Shift pan by `dy` screen px without painting, so a caller can hold a
     * row still across a relayout. The next `reapply()` clamps and paints.
     */
    nudgePan: (dy: number) => {
      panY += dy;
    },

    /** Jump to the top of the tree, keeping the current zoom and grain. */
    panToTop: () => {
      if (!enabled) return;
      panY = LEFT_PAD;
      dirty = true;
      apply();
    },

    reapply: () => {
      reapplySoft();
    },

    destroy: () => {
      enabled = false;
      viewport.removeEventListener("wheel", onWheel);
      viewport.removeEventListener("pointerdown", onPointerDown);
      viewport.removeEventListener("pointermove", onPointerMove);
      viewport.removeEventListener("pointerup", onPointerUp);
      viewport.removeEventListener("pointercancel", onPointerUp);
      viewport.removeEventListener("dblclick", onDblClick);
      viewport.classList.remove("is-camera-on", "is-panning");
      setMapView(mapEl, "text");
      clearMapViewPin(mapEl);
    },
  };
}

// 6. Utilities

function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n));
}
