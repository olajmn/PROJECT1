// Shared helpers for the Manager id menu.

import { setProjectUser } from "../../api.js";
import type { ProjectView } from "../../types.js";

export function closeIdCardMenus(): void {
  document.querySelectorAll(".sidebar-id-card-menu").forEach((el) => {
    (el as HTMLElement).hidden = true;
  });
  document.querySelectorAll(".sidebar-id-card-menu-toggle").forEach((el) => {
    el.setAttribute("aria-expanded", "false");
  });
}

let idCardMenuCloserInstalled = false;

/** One document listener — close any open id-card ⋯ menu on outside click. */
export function ensureIdCardMenuCloser(): void {
  if (idCardMenuCloserInstalled) return;
  idCardMenuCloserInstalled = true;
  document.addEventListener("click", () => closeIdCardMenus());
}

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
