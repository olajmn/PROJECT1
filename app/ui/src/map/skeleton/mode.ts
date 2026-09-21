/**
 * Map view mode: Text (beads) vs Line (diagram).
 *
 * Separate from camera zoom limits:
 * - Zoom ≤ ENTER → Line (text too small)
 * - Zoom > EXIT  → Text (readable again)
 * - Between: hysteresis, keep current
 *
 * Toolbar sets the view immediately and pins it. Auto sync does not
 * undo that choice until zoom crosses the opposite threshold (or
 * overview / empty landing clears the pin).
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

/**
 * Sync Text|Line from zoom. A toolbar pin keeps the chosen view until
 * zoom enters the opposite auto-zone (then pin clears and auto wins).
 */
export function syncSkeletonFromZoom(
  mapEl: HTMLElement,
  zoom: number,
): void {
  const pinned = isMapViewPinned(mapEl);
  const current = getMapView(mapEl);

  if (zoom <= SKELETON_ENTER) {
    // Auto Line. Honor pinned Text until user zooms back into Text zone.
    if (pinned && current === "text") return;
    if (pinned) clearMapViewPin(mapEl);
    setMapView(mapEl, "skeleton");
    return;
  }
  if (zoom > SKELETON_EXIT) {
    // Auto Text. Honor pinned Line until user zooms into Line zone.
    if (pinned && current === "skeleton") return;
    if (pinned) clearMapViewPin(mapEl);
    setMapView(mapEl, "text");
  }
}
