// Local project order under an active id#N.
// Global project_id stays the wire identity; sidebar shows #1..#n
// (oldest = 1) with the real id in parentheses.

// Contents
//  1. Order
//      - projectsChronologicalForUser()
//      - projectsNewestFirst()
//  2. Labels
//      - localOrdinal()
//      - projectListIdLabel()

import type { ProjectView } from "../types.js";

// 1. Order

/** Active user's projects, oldest-first (local #1 = first created). */
export function projectsChronologicalForUser(
  projects: ProjectView[],
  userId: number | null,
): ProjectView[] {
  if (userId === null) return [];
  return projects
    .filter((p) => p.sim_user_id === userId)
    .slice()
    .sort((a, b) => a.project_id - b.project_id);
}

/** Newest on top for sidebar display. */
export function projectsNewestFirst(
  chronological: ProjectView[],
): ProjectView[] {
  return chronological.slice().reverse();
}

// 2. Labels

/** 1-based index in chronological (oldest-first) order. */
export function localOrdinal(
  chronological: ProjectView[],
  projectId: number,
): number {
  return chronological.findIndex((p) => p.project_id === projectId) + 1;
}

/** e.g. `#3 (#49)` — local sequence, then wire id. */
export function projectListIdLabel(
  chronological: ProjectView[],
  project: ProjectView,
): string {
  const ordinal = localOrdinal(chronological, project.project_id);
  return `#${ordinal} (#${project.project_id})`;
}
