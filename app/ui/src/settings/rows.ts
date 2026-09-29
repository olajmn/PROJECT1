// Settings rows: a small grey section title over a quiet group of rows,
// each a label on the left and a value, control, or actions on the right
// (like system settings). Replaces register/ page by page — see TODO.md
// § Parallel paths. Styles: css/settings/rows.css

// Contents
//  1. Builders
//      - settingsSection()
//      - settingsGroup()
//      - settingsRow()
//      - settingsListRow()
//      - settingsAction()
//  2. Formatting
//      - shortDate()

// 1. Builders

/** A section: small grey title, then its groups. */
export function settingsSection(title: string, ...groups: HTMLElement[]): HTMLElement {
  const section = document.createElement("section");
  section.className = "settings-section";
  const heading = document.createElement("h2");
  heading.className = "settings-section-title";
  heading.textContent = title;
  section.append(heading, ...groups);
  return section;
}

/** A rounded group of rows with a hairline between them. */
export function settingsGroup(rows: HTMLElement[]): HTMLElement {
  const group = document.createElement("div");
  group.className = "settings-group";
  group.append(...rows);
  return group;
}

/** One row: `label` left; `value` (text or element) after it; `end`
 *  (controls or actions) at the right edge. */
export function settingsRow(
  label: string | Node,
  value?: string | Node,
  end?: Node[],
): HTMLElement {
  const row = document.createElement("div");
  row.className = "settings-item";
  const labelEl = document.createElement("span");
  labelEl.className = "settings-item-label";
  labelEl.append(label);
  row.appendChild(labelEl);
  if (value !== undefined) {
    const valueEl = document.createElement("span");
    valueEl.className = "settings-item-value";
    valueEl.append(value);
    row.appendChild(valueEl);
  }
  if (end && end.length) {
    const endEl = document.createElement("span");
    endEl.className = "settings-item-end";
    endEl.append(...end);
    row.appendChild(endEl);
  }
  return row;
}

/** A list row (Archive, Directory): the item's name in the text colour,
 *  its details grey after it, actions at the right edge. */
export function settingsListRow(
  name: string,
  details: string,
  end?: Node[],
): HTMLElement {
  const row = settingsRow(name, details, end);
  row.classList.add("is-list");
  return row;
}

/** A small action button for a row's right edge; `danger` makes it red
 *  (delete). */
export function settingsAction(
  label: string,
  onClick: (button: HTMLButtonElement) => void,
  danger = false,
): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = danger ? "settings-action is-danger" : "settings-action";
  button.textContent = label;
  button.addEventListener("click", () => onClick(button));
  return button;
}

// 2. Formatting

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "28 Sep 2026" — dates in Settings rows, the same shape as Current
 *  state (backend/project/status/build_status.py). Spelled out here
 *  rather than toLocaleDateString, which gives "Sept" in some browsers. */
export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return "";
  return `${when.getDate()} ${MONTHS[when.getMonth()]} ${when.getFullYear()}`;
}
