// Directory — Settings → Directory page body.
//
// Shape: ../paragraphs/registerTemplate.ts

// Contents
//  1. Helpers
//  2. mountDirectory()

import { fetchProjects, fetchUsers } from "../../api.js";
import { projectsChronologicalForUser } from "../../panes/create/projectOrder.js";
import { getActiveUserId } from "../../user/activeId.js";
import type { ProjectView, UserView } from "../../dataShapes.js";
import {
  arrangeGroup,
  idGroup,
  orphanGroup,
  startAgeClock,
  type ProjectValues,
} from "../paragraphs/index.js";

// 1. Helpers

function displayLabel(user: UserView): string {
  if (user.text && user.text.trim() && user.text !== "user") {
    return user.text.trim();
  }
  return `id#${user.id}`;
}

function projectValues(project: ProjectView): ProjectValues {
  return {
    id: project.project_id,
    goal: project.goal,
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

/** Fill a `.settings-register` host from users/projects via directorySpec. */
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
      fetchProjects(),
    ]);
    const active = users.filter((u) => !u.archived);
    const uiActiveId = getActiveUserId();
    const orphans = projects.filter((p) => p.sim_user_id === null);
    empty.hidden = active.length > 0 || orphans.length > 0;
    if (active.length === 0 && orphans.length === 0) return;

    for (const user of active) {
      const linked = projectsChronologicalForUser(projects, user.id);
      stack.appendChild(
        arrangeGroup(
          idGroup({
            id: user.id,
            label: displayLabel(user),
            created: user.created_at,
            active: uiActiveId === user.id,
            projects: linked.map(projectValues),
          }),
        ),
      );
    }
    if (orphans.length > 0) {
      stack.appendChild(
        arrangeGroup(orphanGroup(orphans.map(projectValues))),
      );
    }
    startAgeClock(host);
  } catch (err) {
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
}
