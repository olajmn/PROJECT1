// Projects shell column resize (sidebar list + chat).
// Cursor/Notion-style: never collapse to zero; widths in localStorage.

type ColumnResizeOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  cssVar: string;
  storageKey: string;
  defaultWidth: number;
  minWidth: number;
  maxWidthCap: number;
  /** Leave at least this much for the rest of the container. */
  minOther: number;
  /** How pointer X maps to the column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
  bodyClass: string;
};

function installColumnResize(opts: ColumnResizeOpts): void {
  const apply = (px: number) => {
    const max = Math.min(
      opts.maxWidthCap,
      Math.max(opts.minWidth, opts.container.clientWidth - opts.minOther),
    );
    const clamped = Math.min(max, Math.max(opts.minWidth, Math.round(px)));
    opts.container.style.setProperty(opts.cssVar, `${clamped}px`);
    return clamped;
  };

  const stored = Number(localStorage.getItem(opts.storageKey));
  apply(Number.isFinite(stored) && stored > 0 ? stored : opts.defaultWidth);

  let dragging = false;

  const onMove = (event: PointerEvent) => {
    if (!dragging) return;
    apply(opts.widthFromPointer(event.clientX, opts.container.getBoundingClientRect()));
  };

  const onUp = (event: PointerEvent) => {
    if (!dragging) return;
    dragging = false;
    opts.handle.releasePointerCapture(event.pointerId);
    document.body.classList.remove(opts.bodyClass);
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) {
      localStorage.setItem(opts.storageKey, String(Math.round(px)));
    }
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    dragging = true;
    opts.handle.setPointerCapture(event.pointerId);
    document.body.classList.add(opts.bodyClass);
  });
  opts.handle.addEventListener("pointermove", onMove);
  opts.handle.addEventListener("pointerup", onUp);
  opts.handle.addEventListener("pointercancel", onUp);

  window.addEventListener("resize", () => {
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) apply(px);
  });
}

const CHAT_STORAGE_KEY = "projects.chatWidthPx";
const CHAT_DEFAULT = 360;
const CHAT_MIN = 240;
const CHAT_MAX_CAP = 720;
const CHAT_MIN_MAIN = 280;

export function installChatResize(
  workspace: HTMLElement,
  handle: HTMLElement,
): void {
  installColumnResize({
    container: workspace,
    handle,
    cssVar: "--chat-width",
    storageKey: CHAT_STORAGE_KEY,
    defaultWidth: CHAT_DEFAULT,
    minWidth: CHAT_MIN,
    maxWidthCap: CHAT_MAX_CAP,
    minOther: CHAT_MIN_MAIN,
    widthFromPointer: (clientX, rect) => rect.right - clientX,
    bodyClass: "is-resizing-chat",
  });
}

const SIDEBAR_STORAGE_KEY = "projects.sidebarWidthPx";
const SIDEBAR_DEFAULT = 240;
const SIDEBAR_MIN = 180;
const SIDEBAR_MAX_CAP = 420;
/** Leave at least this much for map + chat. */
const SIDEBAR_MIN_REST = 480;

export function installSidebarResize(
  shell: HTMLElement,
  handle: HTMLElement,
): void {
  installColumnResize({
    container: shell,
    handle,
    cssVar: "--sidebar-width",
    storageKey: SIDEBAR_STORAGE_KEY,
    defaultWidth: SIDEBAR_DEFAULT,
    minWidth: SIDEBAR_MIN,
    maxWidthCap: SIDEBAR_MAX_CAP,
    minOther: SIDEBAR_MIN_REST,
    widthFromPointer: (clientX, rect) => clientX - rect.left,
    bodyClass: "is-resizing-sidebar",
  });
}
