// Height drag on the chat chart — same separator idiom as
// Manager | Projects (`sidebar/idMenu/resize.ts`).
//
// Contents
//  1. Stored height
//      - applyStoredChartHeight()
//  2. Drag
//      - installChartResize()

const HEIGHT_KEY = "projects.chartHeightPx";
const MIN_CHART_HEIGHT = 0;
const MIN_THREAD_HEIGHT = 80;
const FALLBACK_MAX_HEIGHT = 360;

// 1. Stored height

function maxChartHeight(map: HTMLElement): number {
  const chat = map.closest(".project-chat");
  if (!(chat instanceof HTMLElement)) return FALLBACK_MAX_HEIGHT;
  const thread = chat.querySelector(".goal-thread");
  const chartH = map.getBoundingClientRect().height;
  const threadH =
    thread instanceof HTMLElement ? thread.getBoundingClientRect().height : 0;
  const steal = Math.max(0, threadH - MIN_THREAD_HEIGHT);
  return Math.max(MIN_CHART_HEIGHT, Math.floor(chartH + steal));
}

function applyChartHeight(map: HTMLElement, px: number): void {
  map.style.height = `${px}px`;
  map.style.maxHeight = `${px}px`;
}

function storedHeight(): number {
  const h = Number(localStorage.getItem(HEIGHT_KEY));
  return Number.isFinite(h) && h >= 0 ? h : NaN;
}

export function applyStoredChartHeight(
  map: HTMLElement,
  opts?: { clampToContent?: boolean },
): void {
  const h = storedHeight();
  if (!Number.isFinite(h)) return;
  map.style.height = "";
  map.style.maxHeight = "";
  const capped = Math.min(maxChartHeight(map), h);
  if (opts?.clampToContent === false) {
    // Empty pane (no talk on this project): keep the pin so the
    // handle stays usable when switching projects.
    applyChartHeight(map, capped);
    return;
  }
  const content = map.scrollHeight;
  // May be shorter than the tree (handle under Talk) but not taller
  // than the tree (empty void under the last bead).
  applyChartHeight(map, Math.min(capped, content));
}

// 2. Drag

export function installChartResize(
  map: HTMLElement,
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
    startH = map.getBoundingClientRect().height;
    maxH = maxChartHeight(map);
    document.body.classList.add("is-resizing-chart");
  });

  handle.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    const nextH = Math.min(
      maxH,
      Math.max(
        MIN_CHART_HEIGHT,
        Math.round(startH + (event.clientY - startY)),
      ),
    );
    applyChartHeight(map, nextH);
  });

  const end = (event: PointerEvent) => {
    if (!dragging) return;
    dragging = false;
    handle.releasePointerCapture(event.pointerId);
    document.body.classList.remove("is-resizing-chart");
    try {
      localStorage.setItem(
        HEIGHT_KEY,
        String(Math.round(map.getBoundingClientRect().height)),
      );
    } catch {
      /* private mode / quota — pin is best-effort */
    }
  };
  handle.addEventListener("pointerup", end);
  handle.addEventListener("pointercancel", end);
}
