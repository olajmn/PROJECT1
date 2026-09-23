// Optional height drag on the id-menu list.

const HEIGHT_KEY = "projects.idMenuListHeightPx";
const MIN_LIST_HEIGHT = 120;
/** Only for a list not in the sidebar yet — no frame to measure. */
const FALLBACK_MAX_HEIGHT = 560;

/**
 * Ceiling for one drag: current list height plus what can still be stolen
 * from .project-list and the Settings auto-margin. maxHeight alone cannot
 * grow past content; this pairs with applyListHeight() setting height.
 * What keeps Projects header / "+" / Settings visible is CSS — those are
 * flex: 0 0 auto; .project-list yields first (see css/sidebar/sidebar.css).
 */
function maxListHeight(list: HTMLElement): number {
  const sidebar = list.closest(".sidebar");
  if (!(sidebar instanceof HTMLElement)) return FALLBACK_MAX_HEIGHT;

  const more = sidebar.querySelector(".sidebar-more");
  if (!(more instanceof HTMLElement)) {
    const frame = sidebar.clientHeight;
    return frame > MIN_LIST_HEIGHT ? frame : FALLBACK_MAX_HEIGHT;
  }

  const listH = list.getBoundingClientRect().height;
  const projectList = sidebar.querySelector(".project-list");
  const projectListH =
    projectList instanceof HTMLElement
      ? projectList.getBoundingClientRect().height
      : 0;

  // Slack above Settings (margin-top: auto on .sidebar-more).
  const createOpen = sidebar.querySelector("#create-open");
  const slackTop =
    createOpen instanceof HTMLElement
      ? createOpen.getBoundingClientRect().bottom
      : list.getBoundingClientRect().bottom;
  const marginSlack = Math.max(0, more.getBoundingClientRect().top - slackTop);

  const maxH = Math.floor(listH + projectListH + marginSlack);
  return Math.max(MIN_LIST_HEIGHT, maxH);
}

/** Pin the list box to px — height forces growth past content; maxHeight
 * stops flex from stretching it further. */
function applyListHeight(list: HTMLElement, px: number): void {
  list.style.height = `${px}px`;
  list.style.maxHeight = `${px}px`;
}

/** Optional pin only — default is natural height (shows everything). */
export function applyStoredHeight(list: HTMLElement): void {
  const h = Number(localStorage.getItem(HEIGHT_KEY));
  if (!Number.isFinite(h) || h < MIN_LIST_HEIGHT) return;
  const capped = Math.min(maxListHeight(list), h);
  applyListHeight(list, capped);
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
    applyListHeight(list, nextH);
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
