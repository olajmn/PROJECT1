/**
 * Chat placeholder when a map node is selected.
 */

/** Placeholder for the focused node label — e.g. `Talk about 2…`. */
export function focusPathPlaceholder(label: string): string {
  const name = (label || "").trim() || "this";
  return `Talk about ${name}…`;
}
