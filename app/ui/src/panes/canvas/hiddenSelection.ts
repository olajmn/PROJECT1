// When the selected node sits deeper than the map's current depth (− / +),
// its row is hidden. Rather than unfold the map, the nearest visible
// ancestor is marked as holding the selection, so picking a node from the
// chat (an About frame) still shows where it is. Runs after a selection
// and after every depth change.

const MARK = "has-hidden-selection";

export function markHiddenSelection(mapEl: ParentNode): void {
  mapEl.querySelectorAll(`.progress-row.${MARK}`).forEach((row) => {
    row.classList.remove(MARK);
  });
  let row = mapEl.querySelector(
    ".progress-row.is-selected.is-grain-hidden",
  ) as HTMLElement | null;
  while (row && row.classList.contains("is-grain-hidden")) {
    const parentId = row.dataset.parentId;
    row = parentId
      ? (mapEl.querySelector(
          `.progress-row[data-step-id="${CSS.escape(parentId)}"]`,
        ) as HTMLElement | null)
      : null;
  }
  row?.classList.add(MARK);
}
