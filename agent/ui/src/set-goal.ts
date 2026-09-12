// The Set Goal page - the explicit action Active's cards can't be:
// starting something genuinely new. Posts to /api/goals (see
// server.py's own docstring - skips Node 1/2/3, same as Active's
// feedback path), then sends the browser to Active to see the result
// as a card, rather than showing it inline here.

import { createGoal } from "./api.js";

const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const button = form.querySelector("button") as HTMLButtonElement;
const error = document.getElementById("error") as HTMLParagraphElement;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  input.disabled = true;
  button.disabled = true;
  error.hidden = true;

  try {
    await createGoal(text);
    window.location.href = "active.html";
  } catch (err) {
    input.disabled = false;
    button.disabled = false;
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
});

input.focus();
