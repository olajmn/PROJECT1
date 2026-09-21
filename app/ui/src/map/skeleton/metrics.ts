/**
 * Line-view thresholds. Word-bar floor lives here; paint is in `lines/`.
 */

/** Enter Line (auto) at/below this zoom when view is unpinned. */
export const SKELETON_ENTER = 0.2;
/** Leave Line (auto) above this — hysteresis when unpinned. */
export const SKELETON_EXIT = 0.26;

/** Floor for a word-bar when the bead is tiny (+, empty, etc.). */
export const MIN_WORD_PX = 8;
