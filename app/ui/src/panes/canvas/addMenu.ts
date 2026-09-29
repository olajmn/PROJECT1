// The "Add" button in the bar under the map: one menu for the ways to add
// many nodes at once (paste an outline, a folder, a saved tree), instead
// of one button each. Reuses the node ⋯ menu's look (.progress-menu) and
// placement (placePopover.ts).

// Contents
//  1. Types
//  2. Public API
//      - buildAddMenu()
//  3. Open / close

import { setTip } from "../../shell/tip.js";
import { placePopover } from "./placePopover.js";

// 1. Types

export type AddMenuItem = {
  label: string;
  detail: string;
  run: (anchor: HTMLElement) => void;
};

// 2. Public API

export function buildAddMenu(items: AddMenuItem[]): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "map-copy-button map-add-button";
  button.textContent = "+ Add";
  // At the bar's left edge: label starts at the button, not centred.
  setTip(button, "Add many nodes", "above", "start");
  button.setAttribute("aria-haspopup", "true");
  button.setAttribute("aria-expanded", "false");

  button.addEventListener("click", () => {
    if (openMenu) {
      closeMenu();
      return;
    }
    const menu = document.createElement("div");
    menu.className = "progress-menu";
    menu.setAttribute("role", "menu");
    for (const item of items) {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "progress-menu-item";
      row.textContent = item.label;
      row.title = item.detail;
      row.addEventListener("click", () => {
        closeMenu();
        item.run(button);
      });
      menu.appendChild(row);
    }
    document.body.appendChild(menu);
    placePopover(menu, button.getBoundingClientRect());
    openMenu = menu;
    openButton = button;
    button.setAttribute("aria-expanded", "true");
    document.addEventListener("click", onOutside, true);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", closeMenu);
  });

  return button;
}

// 3. Open / close

let openMenu: HTMLElement | null = null;
let openButton: HTMLElement | null = null;

/** Outside click closes; a click on the button is left to its own
 *  handler, which toggles. */
function onOutside(event: MouseEvent): void {
  const target = event.target as Node;
  if (!openMenu || openMenu.contains(target)) return;
  if (openButton?.contains(target)) return;
  closeMenu();
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "Escape") closeMenu();
}

function closeMenu(): void {
  if (!openMenu) return;
  openMenu.remove();
  openButton?.setAttribute("aria-expanded", "false");
  openMenu = null;
  openButton = null;
  document.removeEventListener("click", onOutside, true);
  document.removeEventListener("keydown", onKey);
  window.removeEventListener("resize", closeMenu);
}
