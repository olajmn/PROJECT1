// Place a fixed-position popover (the node ⋯ menu, the saved-tree
// picker) under its anchor, flipping above or left when it would leave
// the window. Popovers live on <body>: the map stage is CSS-transformed,
// which would make position: fixed relative to the stage instead.

const GAP = 4;
const EDGE = 8;

/** Call with the popover already in the DOM and visible. Without an
 *  anchor it goes near the top-left corner. */
export function placePopover(popover: HTMLElement, anchor: DOMRect | null): void {
  popover.style.left = `${Math.round(anchor?.left ?? 16)}px`;
  popover.style.top = `${Math.round((anchor?.bottom ?? 16) + GAP)}px`;
  requestAnimationFrame(() => {
    const box = popover.getBoundingClientRect();
    if (anchor && box.bottom > window.innerHeight - EDGE) {
      popover.style.top = `${Math.max(EDGE, Math.round(anchor.top - box.height - GAP))}px`;
    }
    if (box.right > window.innerWidth - EDGE) {
      popover.style.left = `${Math.max(EDGE, Math.round(window.innerWidth - box.width - EDGE))}px`;
    }
  });
}
