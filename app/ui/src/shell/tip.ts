// Quick hover label for buttons that show only a symbol or an icon.
// Drawn by CSS from data-tip (css/shared.css), so it appears faster and
// in the app's own look, unlike the browser's delayed `title` tooltip,
// which is not set as well (it would show a second label).

export type TipPlace = "above" | "below";
export type TipAlign = "start" | "center" | "end";

export function setTip(
  el: HTMLElement,
  text: string,
  place: TipPlace = "above",
  align: TipAlign = "center",
): void {
  el.removeAttribute("title");
  el.dataset.tip = text;
  el.dataset.tipPlace = place;
  el.dataset.tipAlign = align;
  el.setAttribute("aria-label", text);
  // Pressing the button hides the label until the pointer leaves it, so
  // it does not sit over what the click opened. Wired once per element
  // (setTip may be called again to change the text).
  if (el.dataset.tipWired) return;
  el.dataset.tipWired = "1";
  el.addEventListener("pointerdown", () => el.classList.add("tip-off"));
  el.addEventListener("pointerleave", () => el.classList.remove("tip-off"));
}
