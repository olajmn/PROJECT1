// Project order helpers under an account.
// Global project_id stays the wire identity; sticky account_n is the
// map/chrome `#N` (persisted; delete does not renumber).

// Contents
//  1. Order
//      - projectsChronologicalForUser()
//      - projectsNewestFirst()
//  2. Labels (map chrome / Directory)
//      - projectChromeHash()
//      - projectListIdLabel()

import type { ProjectView } from "../../dataShapes.js";

// 1. Order

/** Active user's projects, oldest-first (by sticky account_n, then wire id). */
export function projectsChronologicalForUser(
  projects: ProjectView[],
  userId: number | null,
): ProjectView[] {
  if (userId === null) return [];
  return projects
    .filter((p) => p.sim_user_id === userId)
    .slice()
    .sort((a, b) => {
      const an = a.account_n ?? Number.POSITIVE_INFINITY;
      const bn = b.account_n ?? Number.POSITIVE_INFINITY;
      if (an !== bn) return an - bn;
      return a.project_id - b.project_id;
    });
}

/** Newest on top for sidebar display. */
export function projectsNewestFirst(
  chronological: ProjectView[],
): ProjectView[] {
  return chronological.slice().reverse();
}

// 2. Labels

/** Map bead / copy chrome: sticky `#N`, else wire id while backfill catches up. */
export function projectChromeHash(project: ProjectView): string {
  const n = project.account_n;
  return n != null ? `#${n}` : `#${project.project_id}`;
}

/** Directory-style inspect: `#3 · global 49`. */
export function projectListIdLabel(project: ProjectView): string {
  const n = project.account_n;
  if (n != null) return `#${n} · global ${project.project_id}`;
  return `global ${project.project_id}`;
}
