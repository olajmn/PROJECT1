// Chat chart pane — derived talk tree in the chat column.
// The Talk brand toggles the panel, same as Manager: open/height are
// shell-global (localStorage), not per project. The tree still comes
// from the active project's `talk`; an open empty pane keeps the
// resize handle so the pin survives project switches.
//
// Contents
//  1. Types
//      - ChatChart
//  2. Public API
//      - createChatChart()

import type { TalkSequence } from "../../types.js";
import { applyStoredChartHeight, installChartResize } from "./resize.js";
import { chartId, openChartId, renderChartTree } from "./tree.js";

const OPEN_KEY = "projects.chartOpen";

// 1. Types

export type ChatChart = {
  fill: (
    sequences: TalkSequence[],
    onPick: (sequence: TalkSequence) => void,
  ) => void;
  clearSelection: () => void;
};

// 2. Public API

export function createChatChart(
  map: HTMLElement,
  handle: HTMLElement,
  toggle: HTMLButtonElement,
): ChatChart {
  installChartResize(map, handle);

  let selectedStart: number | null = null;
  let lastSequences: TalkSequence[] = [];
  let lastOnPick: ((sequence: TalkSequence) => void) | null = null;
  let open = readOpen();

  toggle.hidden = false;
  toggle.addEventListener("click", () => setOpen(!open));

  function rememberOpen(next: boolean): void {
    try {
      localStorage.setItem(OPEN_KEY, next ? "1" : "0");
    } catch {
      /* private mode / quota — open state is best-effort */
    }
  }

  function setOpen(next: boolean): void {
    open = next;
    rememberOpen(next);
    if (lastOnPick) fill(lastSequences, lastOnPick);
    else paintChrome([], null);
  }

  function paintChrome(
    sequences: TalkSequence[],
    onPick: ((sequence: TalkSequence) => void) | null,
  ): void {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.classList.toggle("is-active", open);
    map.innerHTML = "";
    if (!open) {
      map.hidden = true;
      handle.hidden = true;
      return;
    }
    map.hidden = false;
    handle.hidden = false;
    if (sequences.length === 0 || !onPick) {
      // Keep the stored height across projects with no talk yet, so
      // the handle stays draggable instead of collapsing to a line.
      applyStoredChartHeight(map, { clampToContent: false });
      return;
    }
    const selectedId =
      selectedStart == null ? openChartId(sequences) : chartId(selectedStart);
    map.appendChild(
      renderChartTree(sequences, selectedId, (sequence) => {
        selectedStart = sequence.start;
        onPick(sequence);
      }),
    );
    applyStoredChartHeight(map);
  }

  function fill(
    sequences: TalkSequence[],
    onPick: (sequence: TalkSequence) => void,
  ): void {
    lastSequences = sequences;
    lastOnPick = onPick;
    paintChrome(sequences, onPick);
  }

  return {
    fill,
    clearSelection: () => {
      selectedStart = null;
    },
  };
}

function readOpen(): boolean {
  try {
    return localStorage.getItem(OPEN_KEY) === "1";
  } catch {
    return false;
  }
}
