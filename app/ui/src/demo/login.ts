// The demo's login page (login.html): one shared password, then on to
// the app. Only reachable in demo mode (docs/demo.md).

import { logIn } from "../api.js";
import { applyStoredTheme } from "../user/theme.js";

applyStoredTheme();

// Every demo login gets a fresh copy of the data, so it also starts where
// a first visit does: the browser forgets the last project and each
// map's depth and view. Owners of these keys: user/activeAccount.ts
// (lastProjectId:) and panes/canvas/zoomAndPan/frameControls.ts (map…).
// Theme, column widths, and panel states are kept.
const SESSION_KEY_PREFIXES = ["lastProjectId:", "mapGrain:", "mapView:", "mapViewPinned:"];

function forgetLastSession(): void {
  try {
    const keys = Object.keys(localStorage);
    for (const key of keys) {
      if (SESSION_KEY_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        localStorage.removeItem(key);
      }
    }
  } catch {
    // Storage blocked (private mode on some browsers): nothing to forget.
  }
}

const form = document.getElementById("login-form") as HTMLFormElement;
const input = document.getElementById("login-password") as HTMLInputElement;
const button = form.querySelector("button") as HTMLButtonElement;
const error = document.getElementById("login-error") as HTMLParagraphElement;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.textContent = "";
  button.disabled = true;
  try {
    await logIn(input.value);
    forgetLastSession();
    window.location.assign("/");
  } catch (err) {
    error.textContent = (err as Error).message;
    input.select();
  } finally {
    button.disabled = false;
  }
});
