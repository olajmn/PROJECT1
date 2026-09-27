// Height drag on the status panel above the chat — same separator idiom as
// the sidebar / chat column grips (`shell/columnWidths.ts`).
//
// Contents
//  1. Stored height
//      - applyStoredPanelHeight()
//  2. Drag
//      - installPanelResize()

// Key kept from the talk chart this panel replaced, so a pinned height survives.
const HEIGHT_KEY = "projects.chartHeightPx";
const MIN_PANEL_HEIGHT = 0;
const MIN_THREAD_HEIGHT = 80;
const FALLBACK_MAX_HEIGHT = 360;

// 1. Stored height

function maxPanelHeight(panel: HTMLElement): number {
  const chat = panel.closest(".project-chat");
  if (!(chat instanceof HTMLElement)) return FALLBACK_MAX_HEIGHT;
  const thread = chat.querySelector(".chat-thread");
  const panelH = panel.getBoundingClientRect().height;
  const threadH =
    thread instanceof HTMLElement ? thread.getBoundingClientRect().height : 0;
  const steal = Math.max(0, threadH - MIN_THREAD_HEIGHT);
  return Math.max(MIN_PANEL_HEIGHT, Math.floor(panelH + steal));
}

function applyPanelHeight(panel: HTMLElement, px: number): void {
  panel.style.height = `${px}px`;
  panel.style.maxHeight = `${px}px`;
}

function storedHeight(): number {
  const h = Number(localStorage.getItem(HEIGHT_KEY));
  return Number.isFinite(h) && h >= 0 ? h : NaN;
}

export function applyStoredPanelHeight(
  panel: HTMLElement,
  opts?: { clampToContent?: boolean },
): void {
  const h = storedHeight();
  if (!Number.isFinite(h)) return;
  panel.style.height = "";
  panel.style.maxHeight = "";
  const capped = Math.min(maxPanelHeight(panel), h);
  if (opts?.clampToContent === false) {
    // Empty panel (a project with no status yet): keep the pin so the
    // handle stays usable when switching projects.
    applyPanelHeight(panel, capped);
    return;
  }
  const content = panel.scrollHeight;
  // May be shorter than the content (handle under Status) but not taller
  // than the content (no empty space under the last line).
  applyPanelHeight(panel, Math.min(capped, content));
}

// 2. Drag

export function installPanelResize(
  panel: HTMLElement,
  handle: HTMLElement,
): void {
  let dragging = false;
  let startY = 0;
  let startH = 0;
  let maxH = FALLBACK_MAX_HEIGHT;

  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragging = true;
    handle.setPointerCapture(event.pointerId);
    startY = event.clientY;
    startH = panel.getBoundingClientRect().height;
    maxH = maxPanelHeight(panel);
    document.body.classList.add("is-resizing-status");
  });

  handle.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    const nextH = Math.min(
      maxH,
      Math.max(
        MIN_PANEL_HEIGHT,
        Math.round(startH + (event.clientY - startY)),
      ),
    );
    applyPanelHeight(panel, nextH);
  });

  const end = (event: PointerEvent) => {
    if (!dragging) return;
    dragging = false;
    handle.releasePointerCapture(event.pointerId);
    document.body.classList.remove("is-resizing-status");
    try {
      localStorage.setItem(
        HEIGHT_KEY,
        String(Math.round(panel.getBoundingClientRect().height)),
      );
    } catch {
      /* private mode / quota — pin is best-effort */
    }
  };
  handle.addEventListener("pointerup", end);
  handle.addEventListener("pointercancel", end);
}
