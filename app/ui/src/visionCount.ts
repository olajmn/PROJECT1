// Sets the Vision nav link to "Vision (N)" — active, non-archived
// count. Called once by each page entry. Nav markup is duplicated per
// HTML file; the number comes from here so pages stay in sync.
//
// A fetch failure must never block the page: leave the plain HTML
// label alone.

// Contents
//  1. initVisionCount()

import { fetchVisions } from "./api.js";

// 1. initVisionCount()

export async function initVisionCount(): Promise<void> {
  const visionLink = document.querySelector<HTMLAnchorElement>(
    'nav a[href="vision.html"]',
  );

  try {
    const visions = await fetchVisions();
    if (visionLink) {
      const activeVisionCount = visions.filter((v) => !v.archived).length;
      visionLink.textContent = `Vision (${activeVisionCount})`;
    }
  } catch {
    // Leave the plain labels already in the HTML.
  }
}
