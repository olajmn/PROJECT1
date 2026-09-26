// Shared helpers for the Accounts panel.

import { setProjectUser } from "../../../api.js";
import type { ProjectView } from "../../../dataShapes.js";

export async function claimUnassigned(
  userId: number,
  projects: ProjectView[],
): Promise<ProjectView[]> {
  const orphans = projects.filter((p) => p.sim_user_id === null);
  const claimed: ProjectView[] = [];
  for (const orphan of orphans) {
    claimed.push(await setProjectUser(orphan.project_id, userId));
  }
  return claimed;
}

export function showError(host: HTMLElement, err: unknown): void {
  const error = document.createElement("p");
  error.className = "error";
  error.textContent = `(error: ${(err as Error).message})`;
  host.appendChild(error);
}
