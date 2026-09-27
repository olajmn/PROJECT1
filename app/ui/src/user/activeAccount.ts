// Active simulated account seat. Wire: sim_user_id. Display: Accounts /
// account#N (see userLabel / accountWireLabel).

const STORAGE_KEY = "activeSimUserId";

/** Top sidebar brand — opens the accounts panel. */
export const ACCOUNTS_BRAND = "Accounts";

export function getActiveUserId(): number | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw == null || raw === "") return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export function setActiveUserId(id: number | null): void {
  if (id == null) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, String(id));
}

const LAST_PROJECT_KEY_PREFIX = "lastProjectId:";

/** Last project viewed under a given sim user — survives page refresh. */
export function getLastProjectId(userId: number): number | null {
  const raw = localStorage.getItem(LAST_PROJECT_KEY_PREFIX + userId);
  if (raw == null || raw === "") return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export function setLastProjectId(userId: number, projectId: number | null): void {
  if (projectId == null) {
    localStorage.removeItem(LAST_PROJECT_KEY_PREFIX + userId);
    return;
  }
  localStorage.setItem(LAST_PROJECT_KEY_PREFIX + userId, String(projectId));
}

/** Wire id label — always `account#N`, even when a custom name is set. */
export function accountWireLabel(id: number): string {
  return `account#${id}`;
}

/** Display name for one sim user — custom label, or account#N. */
export function userLabel(user: { id: number; text?: string | null }): string {
  const t = user.text?.trim();
  if (t && t !== "user") return t;
  return accountWireLabel(user.id);
}
