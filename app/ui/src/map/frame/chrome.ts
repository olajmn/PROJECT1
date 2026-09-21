/**
 * Map frame chrome: grain −/+ and Text|Line inside `.map-frame`.
 * Camera pan/zoom is separate (`frame/camera`).
 *
 * Grain is stored on the map wrap as `data-map-grain`:
 *   - a depth number → show rows up to that depth
 *   - `"all"` → show every depth (not a view mode; just the attribute
 *     value when grain is unbounded)
 */

import { installMapCamera } from "./camera.js";
import { measureMapContent } from "../lines/svg.js";
import {
  getMapView,
  setMapView,
  type MapView,
} from "../skeleton/mode.js";

/** Max visible depth; `null` = every level → `data-map-grain="all"`. */
type Grain = number | null;

/** `data-map-grain` value when every depth is visible. */
const MAP_GRAIN_ALL = "all";

type Sticky = { grain: Grain; view: MapView; viewPinned: boolean };

const stickyByProject = new Map<number, Sticky>();

/** Prefer this overview scale when picking initial grain. */
const OVERVIEW_READABLE = 0.58;

export type MapScaleHandle = {
  refresh: () => void;
  destroy: () => void;
};

/**
 * Wrap `mapEl` in the map frame + grain/view toolbar.
 * `projectId` remembers grain + view across re-renders.
 */
export function installMapScale(
  body: HTMLElement,
  mapEl: HTMLElement,
  projectId: number,
): MapScaleHandle {
  const sticky = stickyByProject.get(projectId);
  let grain: Grain = sticky?.grain ?? null;
  let grainReady = sticky !== undefined;
  let view: MapView = sticky?.view ?? "text";
  let viewPinned = sticky?.viewPinned ?? false;

  const toolbar = document.createElement("div");
  toolbar.className = "map-scale-toolbar";
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Map grain and view");

  const zoomOutBtn = document.createElement("button");
  zoomOutBtn.type = "button";
  zoomOutBtn.className = "map-scale-btn";
  zoomOutBtn.textContent = "−";
  zoomOutBtn.title = "Show less depth";

  const zoomInBtn = document.createElement("button");
  zoomInBtn.type = "button";
  zoomInBtn.className = "map-scale-btn";
  zoomInBtn.textContent = "+";
  zoomInBtn.title = "Show more depth";

  const viewGroup = document.createElement("div");
  viewGroup.className = "map-scale-view";
  viewGroup.setAttribute("role", "group");
  viewGroup.setAttribute("aria-label", "Map view");

  const textBtn = document.createElement("button");
  textBtn.type = "button";
  textBtn.className = "map-scale-btn";
  textBtn.textContent = "Text";
  textBtn.title = "Bead / text view";

  const lineBtn = document.createElement("button");
  lineBtn.type = "button";
  lineBtn.className = "map-scale-btn";
  lineBtn.textContent = "Line";
  lineBtn.title = "Skeleton line view";

  viewGroup.append(textBtn, lineBtn);
  toolbar.append(zoomOutBtn, zoomInBtn, viewGroup);

  const viewport = document.createElement("div");
  viewport.className = "map-scale-viewport map-frame is-camera-on";
  viewport.setAttribute("data-map-frame", "");

  const slot = document.createElement("div");
  slot.className = "map-scale-slot";

  const stage = document.createElement("div");
  stage.className = "map-scale-stage";

  body.insertBefore(toolbar, mapEl);
  body.insertBefore(viewport, mapEl);
  viewport.appendChild(slot);
  slot.appendChild(stage);
  stage.appendChild(mapEl);

  const syncViewChrome = (): void => {
    const v = getMapView(mapEl);
    textBtn.classList.toggle("is-active", v === "text");
    lineBtn.classList.toggle("is-active", v === "skeleton");
    textBtn.setAttribute("aria-pressed", v === "text" ? "true" : "false");
    lineBtn.setAttribute("aria-pressed", v === "skeleton" ? "true" : "false");
  };

  const remember = (): void => {
    stickyByProject.set(projectId, {
      grain,
      view: getMapView(mapEl),
      viewPinned: mapEl.dataset.mapViewPin === "1",
    });
  };

  const camera = installMapCamera(viewport, slot, stage, mapEl, {
    onChange: () => {
      view = getMapView(mapEl);
      viewPinned = mapEl.dataset.mapViewPin === "1";
      syncViewChrome();
      remember();
    },
  });
  camera.setEnabled(true);

  const applyView = (next: MapView, pinned: boolean): void => {
    view = next;
    viewPinned = pinned;
    setMapView(mapEl, next, { pin: pinned });
  };

  applyView(view, viewPinned);

  const treeMaxDepth = (): number => {
    let max = 0;
    mapEl.querySelectorAll(".progress-row[data-depth]").forEach((el) => {
      const d = Number((el as HTMLElement).dataset.depth || 0);
      if (Number.isFinite(d)) max = Math.max(max, d);
    });
    return max;
  };

  const syncChrome = (): void => {
    const maxD = treeMaxDepth();
    const cur = grain === null ? maxD : grain;
    zoomOutBtn.disabled = cur <= 0;
    zoomInBtn.disabled = cur >= maxD;
    syncViewChrome();
  };

  const applyGrain = (next: Grain): void => {
    grain = next;
    grainReady = true;
    const maxD = treeMaxDepth();
    const limit = next === null ? maxD : next;
    // DOM attribute on `.progress-line` — not a Fit/All view tab.
    mapEl.dataset.mapGrain =
      next === null ? MAP_GRAIN_ALL : String(next);

    mapEl.querySelectorAll(".progress-row[data-depth]").forEach((node) => {
      const row = node as HTMLElement;
      const d = Number(row.dataset.depth || 0);
      row.classList.toggle("is-grain-hidden", d > limit);
    });

    mapEl.querySelectorAll(".progress-row[data-step-id]").forEach((node) => {
      const row = node as HTMLElement;
      if (row.classList.contains("is-grain-hidden")) {
        row.classList.remove("has-grain-more");
        return;
      }
      const id = row.dataset.stepId;
      if (!id) return;
      const child = mapEl.querySelector(
        `.progress-row.is-grain-hidden[data-parent-id="${CSS.escape(id)}"]`,
      );
      row.classList.toggle("has-grain-more", Boolean(child));
    });
  };

  const measureNatural = (): { w: number; h: number } => {
    const prevTransform = stage.style.transform;
    const prevScale = mapEl.dataset.mapScale ?? "1";
    stage.style.transform = "none";
    mapEl.dataset.mapScale = "1";
    const size = measureMapContent(mapEl);
    stage.style.transform = prevTransform;
    mapEl.dataset.mapScale = prevScale;
    return size;
  };

  const frameInner = (): { w: number; h: number } => {
    const cs = getComputedStyle(viewport);
    const pl = parseFloat(cs.paddingLeft) || 0;
    const pr = parseFloat(cs.paddingRight) || 0;
    const pt = parseFloat(cs.paddingTop) || 0;
    const pb = parseFloat(cs.paddingBottom) || 0;
    return {
      w: Math.max(viewport.clientWidth - pl - pr, 1),
      h: Math.max(viewport.clientHeight - pt - pb, 1),
    };
  };

  const pickOverviewGrain = (): Grain => {
    const maxD = treeMaxDepth();
    for (let g = maxD; g >= 0; g--) {
      const candidate: Grain = g === maxD ? null : g;
      applyGrain(candidate);
      const { w, h } = measureNatural();
      const a = frameInner();
      const needed = Math.min(1, a.w / w, a.h / h);
      if (needed >= OVERVIEW_READABLE || g === 0) return candidate;
    }
    return 0;
  };

  const paint = (mode: "overview" | "keep"): void => {
    // Overview always re-picks a readable grain — sticky data-map-grain="all"
    // must not force a hairline fit. Keep uses the user's grain from −/+.
    if (mode === "overview" || !grainReady) {
      const picked = pickOverviewGrain();
      applyGrain(picked);
    } else {
      applyGrain(grain);
    }
    const { w, h } = measureNatural();
    camera.setEnabled(true);
    camera.setContentSize(w, h);
    if (mode === "overview") {
      camera.resetOverview();
    } else {
      camera.reapply();
    }
    view = getMapView(mapEl);
    viewPinned = mapEl.dataset.mapViewPin === "1";
    syncChrome();
    remember();
  };

  const bumpGrain = (delta: 1 | -1): void => {
    const maxD = treeMaxDepth();
    const cur = grain === null ? maxD : grain;
    const next = cur + delta;
    if (next < 0 || next > maxD) {
      syncChrome();
      return;
    }
    grain = next >= maxD ? null : next;
    grainReady = true;
    camera.markDirty();
    paint("keep");
  };

  zoomInBtn.addEventListener("click", () => bumpGrain(1));
  zoomOutBtn.addEventListener("click", () => bumpGrain(-1));

  textBtn.addEventListener("click", () => {
    applyView("text", true);
    camera.markDirty();
    camera.reapply();
    // Second settle after ink/CSS come back (avoids stale nest measure).
    requestAnimationFrame(() => camera.reapply());
    syncChrome();
    remember();
  });

  lineBtn.addEventListener("click", () => {
    applyView("skeleton", true);
    camera.markDirty();
    camera.reapply();
    requestAnimationFrame(() => camera.reapply());
    syncChrome();
    remember();
  });

  const ro = new ResizeObserver(() => {
    paint(camera.isDirty() ? "keep" : "overview");
  });
  ro.observe(viewport);

  requestAnimationFrame(() => {
    paint("overview");
    requestAnimationFrame(() => paint(camera.isDirty() ? "keep" : "overview"));
  });
  window.setTimeout(() => paint(camera.isDirty() ? "keep" : "overview"), 50);

  syncChrome();

  return {
    refresh: () => paint(camera.isDirty() ? "keep" : "overview"),
    destroy: () => {
      ro.disconnect();
      camera.destroy();
    },
  };
}
