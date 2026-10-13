// The demo's login page (login.html): one shared password, then on to
// the app. Only reachable in demo mode (docs/demo.md).

import { logIn } from "../api.js";
import { applyStoredTheme } from "../user/theme.js";

applyStoredTheme();

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
    window.location.assign("/");
  } catch (err) {
    error.textContent = (err as Error).message;
    input.select();
  } finally {
    button.disabled = false;
  }
});
