// Which projects belong to the active account, and which one to open.
// Keeps the active account valid when seats are added or deleted.

// Contents
//  1. Filter
//      - projectsForActiveUser()
//  2. Selection
//      - ensureSelectionInActiveUser()
//  3. Active account
//      - syncActiveUser()
//      - detachArchivedOwners()

import { projectsChronologicalForUser } from "./projectOrder.js";
import {
  getActiveUserId,
  getLastProjectId,
  setActiveUserId,
} from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";

// 1. Filter

/** Projects owned by the active simulated user (sim_user_id). */
export function projectsForActiveUser(projects: ProjectView[]): ProjectView[] {
  return projectsChronologicalForUser(projects, getActiveUserId());
}

// 2. Selection

export type SelectionState = {
  selectedId: number | null;
  selectedNodeId: string | null;
  selectedNodeLabel: string | null;
};

/**
 * If the current selection is not under the active account, pick the
 * last project seen under that account (or newest). Clears node focus
 * when the project changes. Mutates `state` in place.
 */
export function ensureSelectionInActiveUser(
  projects: ProjectView[],
  state: SelectionState,
): void {
  const visible = projectsForActiveUser(projects);
  if (
    state.selectedId !== null
    && visible.some((p) => p.project_id === state.selectedId)
  ) {
    return;
  }
  const activeUserId = getActiveUserId();
  const lastId = activeUserId !== null ? getLastProjectId(activeUserId) : null;
  const resumed = visible.find((p) => p.project_id === lastId);
  state.selectedId = resumed
    ? resumed.project_id
    : visible.length > 0
      ? visible[visible.length - 1].project_id
      : null;
  state.selectedNodeId = null;
  state.selectedNodeLabel = null;
}

// 3. Active account

/** Keep localStorage active account aligned with non-archived users. */
export function syncActiveUser(nextUsers: AccountView[]): void {
  const live = nextUsers.filter((u) => !u.archived);
  const active = getActiveUserId();
  if (active !== null && live.some((u) => u.id === active)) return;
  if (live.length === 0) {
    setActiveUserId(null);
    return;
  }
  setActiveUserId(live.reduce((a, b) => (a.id > b.id ? a : b)).id);
}

/** Clear sim_user_id on projects whose owner account was archived. */
export function detachArchivedOwners(
  projects: ProjectView[],
  users: AccountView[],
): ProjectView[] {
  const activeIds = new Set(
    users.filter((v) => !v.archived).map((v) => v.id),
  );
  return projects.map((p) =>
    p.sim_user_id != null && !activeIds.has(p.sim_user_id)
      ? { ...p, sim_user_id: null }
      : p,
  );
}
