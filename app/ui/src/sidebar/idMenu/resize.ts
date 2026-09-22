// Optional max-height drag on the id-menu list.

const HEIGHT_KEY = "projects.idMenuListHeightPx";
const MIN_LIST_HEIGHT = 120;
const MAX_LIST_HEIGHT = 560;

/** Optional cap only — default is natural height (shows everything). */
export function applyStoredHeight(list: HTMLElement): void {
  const h = Number(localStorage.getItem(HEIGHT_KEY));
  if (!Number.isFinite(h) || h < MIN_LIST_HEIGHT) return;
  const capped = Math.min(MAX_LIST_HEIGHT, h);
  list.style.maxHeight = `${capped}px`;
}

export function installResize(list: HTMLElement, handle: HTMLElement): void {
  let dragging = false;
  let startY = 0;
  let startH = 0;

  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragging = true;
    handle.setPointerCapture(event.pointerId);
    startY = event.clientY;
    startH = list.getBoundingClientRect().height;
    document.body.classList.add("is-resizing-id-menu");
  });

  handle.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    const nextH = Math.min(
      MAX_LIST_HEIGHT,
      Math.max(MIN_LIST_HEIGHT, Math.round(startH + (event.clientY - startY))),
    );
    list.style.maxHeight = `${nextH}px`;
  });

  const end = (event: PointerEvent) => {
    if (!dragging) return;
    dragging = false;
    handle.releasePointerCapture(event.pointerId);
    document.body.classList.remove("is-resizing-id-menu");
    const h = Math.round(list.getBoundingClientRect().height);
    localStorage.setItem(HEIGHT_KEY, String(h));
  };
  handle.addEventListener("pointerup", end);
  handle.addEventListener("pointercancel", end);
}
