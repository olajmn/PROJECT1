// Directory — Settings → Directory page body.
//
// Shape: ./spec.ts. Shared templates: ../paragraphs.ts.

// Contents
//  1. Helpers
//  2. mountDirectory()

import { fetchActiveGoals, fetchUsers } from "../../../api.js";
import {
  localOrdinal,
  projectsChronologicalForUser,
} from "../../../sidebar/projectListOrder.js";
import { getActiveUserId } from "../../../user/activeUser.js";
import type { ProjectView, UserView } from "../../../types.js";
import { renderGroup, startAgeClock } from "../paragraphs/index.js";
import { idGroup, orphanGroup, type ProjectValues } from "./spec.js";

// 1. Helpers

function displayLabel(user: UserView): string {
  if (user.text && user.text.trim() && user.text !== "user") {
    return user.text.trim();
  }
  return `id#${user.id}`;
}

function projectValues(
  chronological: ProjectView[],
  project: ProjectView,
): ProjectValues {
  return {
    id: project.project_id,
    goal: project.goal,
    sidebar: localOrdinal(chronological, project.project_id),
    created: project.created_at,
  };
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// 2. mountDirectory()

/** Fill a `.settings-register` host from users/projects via spec.ts. */
export async function mountDirectory(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const stack = el("div", "settings-register-stack");
  const empty = el("p", "empty-state", "No ids yet.");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(stack, empty, error);

  try {
    const [users, projects] = await Promise.all([
      fetchUsers(),
      fetchActiveGoals(),
    ]);
    const active = users.filter((u) => !u.archived);
    const uiActiveId = getActiveUserId();
    const orphans = projects.filter((p) => p.sim_user_id === null);
    empty.hidden = active.length > 0 || orphans.length > 0;
    if (active.length === 0 && orphans.length === 0) return;

    for (const user of active) {
      const linked = projectsChronologicalForUser(projects, user.id);
      stack.appendChild(
        renderGroup(
          idGroup({
            id: user.id,
            label: displayLabel(user),
            created: user.created_at,
            active: uiActiveId === user.id,
            projects: linked.map((p) => projectValues(linked, p)),
          }),
        ),
      );
    }
    if (orphans.length > 0) {
      stack.appendChild(
        renderGroup(
          orphanGroup(orphans.map((p) => projectValues(orphans, p))),
        ),
      );
    }
    startAgeClock(host);
  } catch (err) {
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
}
