// The demo's login page (login.html): one shared password, then on to
// the app. Only reachable in demo mode (docs/demo.md).

import { logIn } from "../api.js";
import { applyStoredTheme } from "../user/theme.js";

applyStoredTheme();

// Every demo login gets a fresh copy of the data, so it also starts where
// a first visit does: the browser forgets the last project, each map's
// depth and view, and the Current state panel's height and open state
// (so its Changes list shows). Owners of these keys:
// user/activeAccount.ts (lastProjectId:),
// panes/canvas/zoomAndPan/frameControls.ts (map…), and
// panes/chat/statusPanel/ (projects.chartHeightPx, projects.statusOpen).
// Theme and column widths are kept.
const SESSION_KEY_PREFIXES = [
  "lastProjectId:",
  "mapGrain:",
  "mapView:",
  "mapViewPinned:",
  "projects.chartHeightPx",
  "projects.statusOpen",
];

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
