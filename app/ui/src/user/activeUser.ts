// Active simulated user (product display: id#N). Wire: sim_user_id.

const STORAGE_KEY = "activeSimUserId";

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

/** Display form for a sim user id: id#N (distinct from project #N). */
export function userLabel(id: number): string {
  return `id#${id}`;
}
