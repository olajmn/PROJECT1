// Optional max-height drag on the id-menu list.

const HEIGHT_KEY = "projects.idMenuListHeightPx";
const MIN_LIST_HEIGHT = 120;
/** Only for a list not in the sidebar yet — no frame to measure. */
const FALLBACK_MAX_HEIGHT = 560;

/**
 * The ceiling is the sidebar's own height rather than a fixed number:
 * dragging the panel open is meant to be able to reach the bottom of the
 * frame. What keeps it from swallowing the Projects header, the "+" and
 * the Settings bar is CSS, not this number — .project-list gives up its
 * height first and those three don't shrink at all (see .project-list in
 * css/sidebar/sidebar.css). So all this has to do is keep a height
 * stored on a tall window from being restored into a short one.
 */
function maxListHeight(list: HTMLElement): number {
  const frame = list.closest(".sidebar")?.clientHeight ?? 0;
  return frame > MIN_LIST_HEIGHT ? frame : FALLBACK_MAX_HEIGHT;
}

/** Optional cap only — default is natural height (shows everything). */
export function applyStoredHeight(list: HTMLElement): void {
  const h = Number(localStorage.getItem(HEIGHT_KEY));
  if (!Number.isFinite(h) || h < MIN_LIST_HEIGHT) return;
  const capped = Math.min(maxListHeight(list), h);
  list.style.maxHeight = `${capped}px`;
}

export function installResize(list: HTMLElement, handle: HTMLElement): void {
  let dragging = false;
  let startY = 0;
  let startH = 0;
  // Measured once per drag: reading it per pointermove would force a
  // layout on every frame of the drag.
  let maxH = FALLBACK_MAX_HEIGHT;

  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragging = true;
    handle.setPointerCapture(event.pointerId);
    startY = event.clientY;
    startH = list.getBoundingClientRect().height;
    maxH = maxListHeight(list);
    document.body.classList.add("is-resizing-id-menu");
  });

  handle.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    const nextH = Math.min(
      maxH,
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
