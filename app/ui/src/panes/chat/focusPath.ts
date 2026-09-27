/**
 * Chat placeholder and frame names for what the chat is about: a
 * selected map node, or a selected day of changes.
 */

/** Placeholder for the focused node label — e.g. `Talk about 2…`. */
export function focusPathPlaceholder(label: string): string {
  const name = (label || "").trim() || "this";
  return `Talk about ${name}…`;
}

/** "changes on 27 Sep" for a YYYY-MM-DD day — the same wording the
 * backend tags the model's history with (build_status.day_name()). */
export function changesDayName(day: string): string {
  const [y, m, d] = day.split("-").map(Number);
  if (!y || !m || !d || m > 12) return `changes on ${day}`;
  // Fixed names, not toLocaleDateString: some locales write "Sept",
  // and this must match the backend's "%b" exactly.
  const year = y === new Date().getFullYear() ? "" : ` ${y}`;
  return `changes on ${d} ${MONTHS[m - 1]}${year}`;
}

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/** Placeholder while a day of changes is selected. */
export function dayFocusPlaceholder(day: string): string {
  return `Talk about ${changesDayName(day)}…`;
}
