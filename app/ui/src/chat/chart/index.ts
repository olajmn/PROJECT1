// Chat chart pane — derived talk tree in the chat column.
// The Talk brand toggles the panel, same as Manager.
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
  }

  function fill(
    sequences: TalkSequence[],
    onPick: (sequence: TalkSequence) => void,
  ): void {
    lastSequences = sequences;
    lastOnPick = onPick;
    const shown = open && sequences.length > 0;
    toggle.hidden = sequences.length === 0;
    toggle.setAttribute("aria-expanded", shown ? "true" : "false");
    toggle.classList.toggle("is-active", shown);
    map.innerHTML = "";
    if (!shown) {
      map.hidden = true;
      handle.hidden = true;
      return;
    }
    map.hidden = false;
    handle.hidden = false;
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
