/**
 * Map frame chrome: grain −/+ and Text|Line inside `.map-frame`.
 * Camera pan/zoom is separate (`zoomAndPan/panAndZoom.ts`).
 *
 * Grain is stored on the map wrap as `data-map-grain`:
 *   - a depth number → show rows up to that depth
 *   - `"all"` → show every depth (not a view mode; just the attribute
 *     value when grain is unbounded)
 */

/*
 * Contents
 *
 * 1. Module State and Types
 *    - poseByProject
 *    - readSticky()
 *    - writeSticky()
 *
 * 2. Toolbar and Frame DOM
 *
 * 3. View and Camera Sync
 *    - syncViewChrome()
 *    - remember()
 *    - applyView()
 *
 * 4. Grain and Sizing
 *    - treeMaxDepth()
 *    - syncChrome()
 *    - applyGrain()
 *    - measureNatural()
 *    - frameInner()
 *    - anchorRow()
 *    - keepAnchor()
 *    - pickOverviewGrain()
 *
 * 5. Paint Orchestration
 *    - paint()
 *    - bumpGrain()
 *
 * 6. Event Wiring and Public Handle
 */

import { installMapCamera, type CameraPose } from "./panAndZoom.js";
import { measureMapContent } from "../lines/svgHelpers.js";
import {
  getMapView,
  setMapView,
  type MapView,
} from "../lineView/textOrLine.js";

// 1. Module State and Types

/** Max visible depth; `null` = every level → `data-map-grain="all"`. */
type Grain = number | null;

/** `data-map-grain` value when every depth is visible. */
const MAP_GRAIN_ALL = "all";

type Sticky = { grain: Grain; view: MapView; viewPinned: boolean };

/** A row plus the on-screen y it should keep across a relayout. */
type RowAnchor = { row: HTMLElement; top: number };

/** Per-project zoom + pan, for this page load only: carried across
 *  re-renders, while a fresh load still opens at the overview. */
const poseByProject = new Map<number, CameraPose>();

/** Per-project grain/view — `localStorage`-backed, survives page refresh. */
function readSticky(projectId: number): Sticky | undefined {
  const rawGrain = localStorage.getItem(`mapGrain:${projectId}`);
  if (rawGrain === null) return undefined;
  const grain: Grain = rawGrain === MAP_GRAIN_ALL ? null : Number(rawGrain);
  const view: MapView =
    localStorage.getItem(`mapView:${projectId}`) === "skeleton"
      ? "skeleton"
      : "text";
  const viewPinned = localStorage.getItem(`mapViewPinned:${projectId}`) === "1";
  return { grain, view, viewPinned };
}

function writeSticky(projectId: number, sticky: Sticky): void {
  localStorage.setItem(
    `mapGrain:${projectId}`,
    sticky.grain === null ? MAP_GRAIN_ALL : String(sticky.grain),
  );
  localStorage.setItem(`mapView:${projectId}`, sticky.view);
  localStorage.setItem(
    `mapViewPinned:${projectId}`,
    sticky.viewPinned ? "1" : "0",
  );
}

/** Prefer this overview scale when picking initial grain. */
const OVERVIEW_READABLE = 0.58;

export type MapScaleHandle = {
  refresh: () => void;
  destroy: () => void;
};

type ScaleOpts = {
  /** Shows a close control in the top bar. Omitted = no close. */
  onClose?: () => void;
};

/**
 * Wrap `mapEl` in the map frame + grain/view toolbar.
 * `projectId` remembers grain + view across re-renders and page refresh.
 */
export function installMapScale(
  body: HTMLElement,
  mapEl: HTMLElement,
  projectId: number,
  opts: ScaleOpts = {},
): MapScaleHandle {
  const sticky = readSticky(projectId);
  let grain: Grain = sticky?.grain ?? null;
  let grainReady = sticky !== undefined;
  let view: MapView = sticky?.view ?? "text";
  let viewPinned = sticky?.viewPinned ?? false;

  // 2. Toolbar and Frame DOM

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
  toolbar.append(zoomOutBtn, zoomInBtn);

  const viewport = document.createElement("div");
  viewport.className = "map-scale-viewport map-frame is-camera-on";
  viewport.setAttribute("data-map-frame", "");

  // Sticky header inside the frame: the tree pans up underneath it.
  // panAndZoom.ts skips `.map-top-bar` in its interactive check, so pressing
  // here never starts a drag.
  const topBar = document.createElement("div");
  topBar.className = "map-top-bar";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "map-scale-btn";
  closeBtn.textContent = "×";
  closeBtn.title = "Close project";
  closeBtn.setAttribute("aria-label", "Close project");
  closeBtn.hidden = opts.onClose === undefined;

  const topBtn = document.createElement("button");
  topBtn.type = "button";
  topBtn.className = "map-scale-btn";
  topBtn.textContent = "↑";
  topBtn.title = "Back to top";
  topBtn.setAttribute("aria-label", "Back to top");

  const slot = document.createElement("div");
  slot.className = "map-scale-slot";

  const stage = document.createElement("div");
  stage.className = "map-scale-stage";

  toolbar.prepend(closeBtn, topBtn);
  topBar.append(toolbar, viewGroup);

  body.insertBefore(viewport, mapEl);
  viewport.appendChild(slot);
  viewport.appendChild(topBar);
  slot.appendChild(stage);
  stage.appendChild(mapEl);

  // 3. View and Camera Sync

  const syncViewChrome = (): void => {
    const v = getMapView(mapEl);
    textBtn.classList.toggle("is-active", v === "text");
    lineBtn.classList.toggle("is-active", v === "skeleton");
    textBtn.setAttribute("aria-pressed", v === "text" ? "true" : "false");
    lineBtn.setAttribute("aria-pressed", v === "skeleton" ? "true" : "false");
  };

  const remember = (): void => {
    writeSticky(projectId, {
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
      poseByProject.set(projectId, camera.getPose());
    },
  });
  camera.setEnabled(true);

  // Every project update (a node added, a chat reply, `/id`) rebuilds the
  // map and this camera; without this it would come back at 1× zoom.
  const pose = poseByProject.get(projectId);
  if (pose) camera.setPose(pose);

  // A remembered grain means the map is deliberately not at the auto-overview,
  // so it counts as dirty — `paint()` then keeps it instead of re-picking.
  // Double-click clears dirty, which restores auto-pick as the reset gesture.
  if (sticky) camera.markDirty();

  const applyView = (next: MapView, pinned: boolean): void => {
    view = next;
    viewPinned = pinned;
    setMapView(mapEl, next, { pin: pinned });
  };

  applyView(view, viewPinned);

  // 4. Grain and Sizing

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

  /**
   * Topmost row that starts inside the frame, with its on-screen y.
   * A row merely straddling the top edge is a poor anchor: its own new
   * children land between it and the frame, pushing the view down even
   * though the anchor itself held. Only fall back to such a row when
   * nothing starts inside the frame at all.
   */
  const anchorRow = (): RowAnchor | null => {
    const frameTop = viewport.getBoundingClientRect().top;
    const rows = Array.from(
      mapEl.querySelectorAll(".progress-row:not(.is-grain-hidden)"),
    ) as HTMLElement[];
    let straddling: RowAnchor | null = null;
    for (const row of rows) {
      const r = row.getBoundingClientRect();
      if (r.top >= frameTop) return { row, top: r.top };
      if (!straddling && r.bottom >= frameTop) straddling = { row, top: r.top };
    }
    return straddling;
  };

  /**
   * Hold `anchor` at the same on-screen y across a grain change, so new
   * depth unfolds below it instead of shoving it out of view. Must run
   * after the rows are re-hidden but before the camera paints.
   */
  const keepAnchor = (anchor: RowAnchor): void => {
    // A collapse can hide the anchor itself — climb to its nearest
    // still-visible ancestor, which occupies the same spot on screen.
    let row: HTMLElement | null = anchor.row;
    while (row && row.classList.contains("is-grain-hidden")) {
      const parentId: string | undefined = row.dataset.parentId;
      row = parentId
        ? (mapEl.querySelector(
            `.progress-row[data-step-id="${CSS.escape(parentId)}"]`,
          ) as HTMLElement | null)
        : null;
    }
    if (!row) return;
    camera.nudgePan(anchor.top - row.getBoundingClientRect().top);
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

  // 5. Paint Orchestration

  const paint = (mode: "overview" | "keep", anchor?: RowAnchor | null): void => {
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
    if (anchor) keepAnchor(anchor);
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
    const anchor = anchorRow();
    grain = next >= maxD ? null : next;
    grainReady = true;
    camera.markDirty();
    paint("keep", anchor);
  };

  // 6. Event Wiring and Public Handle

  closeBtn.addEventListener("click", () => opts.onClose?.());

  topBtn.addEventListener("click", () => camera.panToTop());

  topBar.addEventListener("click", (event) => {
    // The grain/view buttons live in here too — they handle their own
    // clicks, so only the bare strip means "to the top".
    if ((event.target as Element).closest("button")) return;
    camera.panToTop();
  });

  // Wheel here always means "to the top" — stop it before the camera's own
  // wheel-zoom handler on the viewport sees it.
  topBar.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      event.stopPropagation();
      camera.panToTop();
    },
    { passive: false },
  );

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
    paint(camera.isDirty() ? "keep" : "overview");
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
