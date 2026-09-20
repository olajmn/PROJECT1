// Live age beside Created / Started stamps.

export const AGE_ATTR = "data-created-iso";

let ageTimer: number | null = null;

export function formatStamp(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const yyyy = String(d.getFullYear());
  const hh = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${mm}/${dd}/${yyyy} ${hh}:${min}`;
}

export function formatAge(iso: string, nowMs: number): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  let secs = Math.max(0, Math.floor((nowMs - then) / 1000));
  const days = Math.floor(secs / 86400);
  secs %= 86400;
  const hours = Math.floor(secs / 3600);
  secs %= 3600;
  const mins = Math.floor(secs / 60);
  secs %= 60;
  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m ${secs}s`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function tickAges(root: HTMLElement): void {
  const now = Date.now();
  for (const node of Array.from(
    root.querySelectorAll<HTMLElement>(`[${AGE_ATTR}]`),
  )) {
    const iso = node.getAttribute(AGE_ATTR);
    if (iso) node.textContent = formatAge(iso, now);
  }
}

/** Start (or restart) the live age ticker under `root`. */
export function startAgeClock(root: HTMLElement): void {
  if (ageTimer != null) {
    window.clearInterval(ageTimer);
    ageTimer = null;
  }
  tickAges(root);
  ageTimer = window.setInterval(() => tickAges(root), 1000);
}
