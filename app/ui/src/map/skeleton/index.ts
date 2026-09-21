/**
 * Line / skeleton view — mode flag + auto zoom thresholds.
 * Nest painting for Line lives in `map/lines/paint.ts`.
 */

export { SKELETON_ENTER, SKELETON_EXIT, MIN_WORD_PX } from "./metrics.js";

export type { MapView } from "./mode.js";

export {
  isSkeletonMap,
  getMapView,
  isMapViewPinned,
  setMapView,
  clearMapViewPin,
  syncSkeletonFromZoom,
} from "./mode.js";
