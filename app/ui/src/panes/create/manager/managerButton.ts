// The "Manager" button at the top of the sidebar that opens the id menu.

// Contents
//  1. Public API
//      - renderManagerButton()

import { getActiveUserId, ID_BRAND } from "../../../user/activeId.js";

// 1. Public API

/** Refresh the sidebar brand label and aria (open-state class stays on idMenu). */
export function renderManagerButton(
  brand: HTMLButtonElement,
  idMenuOpen: boolean,
): void {
  const active = getActiveUserId();
  brand.textContent = ID_BRAND;
  if (!idMenuOpen) {
    brand.classList.remove("is-active");
  }
  brand.setAttribute(
    "aria-label",
    active !== null
      ? "Active id. Click to switch or create ids."
      : "No active id. Click to create or pick one.",
  );
}
