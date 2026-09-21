/**
 * Pan + zoom camera inside `.map-frame`.
 * Wheel zoom anchors under the cursor vertically; spine stays left-locked.
 * Pan is clamped so a top gap above the tree is not possible.
 * Furthest out = overview fit; closest in = 1× (natural bead size).
 */

import { installMapLines } from "../lines/install.js";
import { isEmptyMap } from "../lines/svg.js";
import {
  clearMapViewPin,
  setMapView,
  syncSkeletonFromZoom,
} from "../skeleton/mode.js";

const ABS_MIN_ZOOM = 0.08;
const MAX_ZOOM = 1;
const WHEEL_STEP = 1.12;
const LEFT_PAD = 8;

export type MapCameraHandle = {
  setEnabled: (on: boolean) => void;
  setContentSize: (w: number, h: number) => void;
  resetOverview: () => void;
  isDirty: () => boolean;
  markDirty: () => void;
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

  const apply = (): void => {
    if (!enabled) return;
    zoom = clamp(zoom, overviewFloor(), MAX_ZOOM);
    clampPan();
    mapEl.dataset.mapScale = String(zoom);
    syncSkeletonFromZoom(mapEl, zoom);
    stage.style.transformOrigin = "0 0";
    stage.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    installMapLines(mapEl);
    opts.onChange?.();
  };

  /** Grain keep: raise zoom if below floor; do not pull down to overview. */
  const reapplySoft = (): void => {
    if (!enabled) return;
    layoutSlotForCamera();
    const floor = overviewFloor();
    if (zoom < floor) zoom = floor;
    if (zoom > MAX_ZOOM) zoom = MAX_ZOOM;
    clampPan();
    mapEl.dataset.mapScale = String(zoom);
    syncSkeletonFromZoom(mapEl, zoom);
    stage.style.transformOrigin = "0 0";
    stage.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    installMapLines(mapEl);
    opts.onChange?.();
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
    const newZ = clamp(oldZ * factor, overviewFloor(), MAX_ZOOM);
    if (newZ === oldZ) return;
    const cy = (fy - panY) / oldZ;
    zoom = newZ;
    panX = LEFT_PAD;
    panY = fy - cy * newZ;
    dirty = true;
    apply();
  };

  const isInteractive = (target: EventTarget | null): boolean => {
    if (!(target instanceof Element)) return false;
    return Boolean(
      target.closest(
        "button, a, input, textarea, select, label, .progress-menu, .progress-bead-btn, .progress-add",
      ),
    );
  };

  const onWheel = (event: WheelEvent): void => {
    if (!enabled) return;
    event.preventDefault();
    const factor = event.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP;
    zoomAt(factor, pointerInFrame(event.clientX, event.clientY).y);
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
    apply();
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
  };

  const onDblClick = (event: MouseEvent): void => {
    if (!enabled) return;
    if (isInteractive(event.target)) return;
    event.preventDefault();
    fitOverview();
  };

  viewport.addEventListener("wheel", onWheel, { passive: false });
  viewport.addEventListener("pointerdown", onPointerDown);
  viewport.addEventListener("pointermove", onPointerMove);
  viewport.addEventListener("pointerup", onPointerUp);
  viewport.addEventListener("pointercancel", onPointerUp);
  viewport.addEventListener("dblclick", onDblClick);

  return {
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

function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n));
}
