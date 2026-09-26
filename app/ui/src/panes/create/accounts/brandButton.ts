// The "Accounts" brand at the top of the sidebar that opens the panel.

// Contents
//  1. Public API
//      - renderAccountsBrand()

import { getActiveUserId, ACCOUNTS_BRAND } from "../../../user/activeAccount.js";

// 1. Public API

/** Refresh the sidebar brand label and aria (open-state class stays on panel). */
export function renderAccountsBrand(
  brand: HTMLButtonElement,
  panelOpen: boolean,
): void {
  const active = getActiveUserId();
  brand.textContent = ACCOUNTS_BRAND;
  if (!panelOpen) {
    brand.classList.remove("is-active");
  }
  brand.setAttribute(
    "aria-label",
    active !== null
      ? "Active account. Click to switch accounts."
      : "No active account. Click to pick one, or create in Settings → Directory.",
  );
}
