/**
 * Map view mode: Text (beads) vs Line (diagram).
 *
 * Separate from camera zoom limits:
 * - Zoom ≤ ENTER → Line (text too small)
 * - Zoom > EXIT  → Text (readable again)
 * - Between: hysteresis, keep current
 *
 * Toolbar sets the view immediately; the next zoom past a threshold
 * follows the rules above (toolbar pin does not block Line→Text).
 */

import { SKELETON_ENTER, SKELETON_EXIT } from "./metrics.js";

export type MapView = "text" | "skeleton";

export function isSkeletonMap(wrap: HTMLElement): boolean {
  return wrap.classList.contains("is-skeleton");
}

export function getMapView(mapEl: HTMLElement): MapView {
  return isSkeletonMap(mapEl) ? "skeleton" : "text";
}

export function isMapViewPinned(mapEl: HTMLElement): boolean {
  return mapEl.dataset.mapViewPin === "1";
}

/** Set Text or Line. Optional pin is kept for sticky chrome only. */
export function setMapView(
  mapEl: HTMLElement,
  view: MapView,
  opts: { pin?: boolean } = {},
): void {
  mapEl.classList.toggle("is-skeleton", view === "skeleton");
  if (opts.pin !== undefined) {
    mapEl.dataset.mapViewPin = opts.pin ? "1" : "0";
  }
}

export function clearMapViewPin(mapEl: HTMLElement): void {
  mapEl.dataset.mapViewPin = "0";
}

/** Sync Text|Line from zoom — pin does not block either direction. */
export function syncSkeletonFromZoom(
  mapEl: HTMLElement,
  zoom: number,
): void {
  if (zoom <= SKELETON_ENTER) {
    setMapView(mapEl, "skeleton");
    return;
  }
  if (zoom > SKELETON_EXIT) {
    setMapView(mapEl, "text");
  }
}
