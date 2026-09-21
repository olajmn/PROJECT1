// Active simulated user (product display: "id"). Wire: sim_user_id.

const STORAGE_KEY = "activeSimUserId";

/** Top sidebar brand — opens the id overview. */
export const ID_BRAND = "Manager";

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

/** Display name for one sim user — label text, or id#N if none. */
export function userLabel(user: { id: number; text?: string | null }): string {
  const t = user.text?.trim();
  if (t && t !== "user") return t;
  return `id#${user.id}`;
}
