// Shared nav-badge populator, called once by every page's own entry
// script (main.ts, active.ts, set-goal.ts, vision.ts, completed.ts,
// history.ts) - the <nav> markup itself is duplicated per static HTML
// file (no templating here), but the counts it shows come from one
// place so all six pages stay in sync.
//
// Only Vision/Active/Completed get a count - the three that name a
// concrete, countable set of things (Conversation and Set Goal don't;
// History already shows its own count as every entry's key:value
// dump). Vision's count is active (non-archived) visions only, same
// "live, not terminal" scope Active already has by excluding
// completed/cancelled goals.
//
// Independent fetches, not shared with whatever the current page
// already loaded - simpler than threading counts through five
// different page scripts for one shared line, and a failure here
// (caught, silently) must never block the page's own real content.

// Contents
//  1. initNavCounts()

import { fetchActiveGoals, fetchCompletedGoals, fetchVisions } from "./api.js";

// 1. initNavCounts()

export async function initNavCounts(): Promise<void> {
  const visionLink = document.querySelector<HTMLAnchorElement>('nav a[href="vision.html"]');
  const activeLink = document.querySelector<HTMLAnchorElement>('nav a[href="active.html"]');
  const completedLink = document.querySelector<HTMLAnchorElement>('nav a[href="completed.html"]');

  try {
    const [visions, active, completed] = await Promise.all([
      fetchVisions(),
      fetchActiveGoals(),
      fetchCompletedGoals(),
    ]);
    if (visionLink) {
      const activeVisionCount = visions.filter((v) => !v.archived).length;
      visionLink.textContent = `Vision (${activeVisionCount})`;
    }
    if (activeLink) activeLink.textContent = `Active (${active.length})`;
    if (completedLink) completedLink.textContent = `Completed (${completed.length})`;
  } catch {
    // Leave the plain labels already in the HTML - a nav badge is a
    // convenience, not something worth an error message of its own.
  }
}
