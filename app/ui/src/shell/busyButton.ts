// Mark a button as busy (spinner via .is-loading CSS).

export function setButtonBusy(
  button: HTMLButtonElement,
  busy: boolean,
): void {
  button.disabled = busy;
  button.classList.toggle("is-loading", busy);
  if (busy) {
    button.setAttribute("aria-busy", "true");
  } else {
    button.removeAttribute("aria-busy");
  }
}
