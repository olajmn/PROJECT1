/**
 * Dot grid spacing for the map camera: picks a spacing step from the zoom
 * and hands it to css/panes/canvas/dotGrid.css. Each step doubles the
 * world spacing, so the grid keeps a steady on-screen density and every
 * dot shown still sits on the 1× grid (fixed to the tree). A step change
 * fades over a fixed time, not over a zoom range, so the grid never rests
 * half-faded between two steps.
 */

/*
 * Contents
 *
 * 1. Constants
 *
 * 2. Dot Grid
 *    - installDotGrid()
 *    - gapAt()
 */

// 1. Constants

/** Spacing at 1×, and the on-screen band a step stays inside. */
const DOT_GAP = 24;
const GAP_MIN = 12;
/** Slack past the band before the step changes, so zoom jitter at the
 *  edge does not flip steps back and forth. */
const STAY_MIN = 11;
const STAY_MAX = 26;
const FADE_MS = 220;

const VARS = ["--cam-dot-gap", "--cam-dot-in", "--cam-dot-out"];

export type DotGridHandle = {
  place: (zoom: number) => void;
  clear: () => void;
};

// 2. Dot Grid

/**
 * The CSS draws three layers: twice the gap, the gap, half the gap. At
 * rest only the gap layer shows (`in` = 1, `out` = 0). Zooming out a
 * step starts from the old, denser grid (`out` = 1) and fades the extra
 * dots away; zooming in starts from the old, sparser grid (`in` = 0) and
 * fades the new dots in.
 */
export function installDotGrid(viewport: HTMLElement): DotGridHandle {
  let step: number | undefined;
  let frame = 0;

  const set = (name: string, value: string): void => {
    viewport.style.setProperty(name, value);
  };

  /** Stop any fade and show only the gap layer. */
  const rest = (): void => {
    cancelAnimationFrame(frame);
    set("--cam-dot-in", "1");
    set("--cam-dot-out", "0");
  };

  /** Animate `name` from `from` to its rest value `to` over `FADE_MS`. */
  const fade = (name: string, from: number, to: number): void => {
    rest();
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.min((now - start) / FADE_MS, 1);
      const eased = 1 - (1 - t) * (1 - t);
      set(name, String(from + (to - from) * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    set(name, String(from));
    frame = requestAnimationFrame(tick);
  };

  return {
    place: (zoom: number) => {
      let next = step;
      const gap = next === undefined ? 0 : gapAt(zoom, next);
      if (next === undefined || gap < STAY_MIN || gap >= STAY_MAX) {
        next = 0;
        while (gapAt(zoom, next) < GAP_MIN) next++;
      }
      if (step !== undefined && next === step + 1) fade("--cam-dot-out", 1, 0);
      else if (step !== undefined && next === step - 1) fade("--cam-dot-in", 0, 1);
      // First paint, or a jump of several steps (a reset): no fade.
      else if (next !== step) rest();
      step = next;
      set("--cam-dot-gap", `${gapAt(zoom, next)}px`);
    },

    clear: () => {
      cancelAnimationFrame(frame);
      step = undefined;
      for (const name of VARS) viewport.style.removeProperty(name);
    },
  };
}

/** On-screen spacing at `zoom` for step `k` (world spacing × 2^k). */
function gapAt(zoom: number, k: number): number {
  return DOT_GAP * zoom * 2 ** k;
}
