/**
 * Spotify-style default names: "New project 1", "New project 2", …
 * Bare "New project" / "New project #1" count when scanning titles.
 */

const NEW_PROJECT_RE = /^new project(?: #?(\d+))?$/i;

/** Next unused `New project N` given existing project titles. */
export function nextNewProjectName(titles: string[]): string {
  let max = 0;
  for (const raw of titles) {
    const m = raw.trim().match(NEW_PROJECT_RE);
    if (!m) continue;
    const n = m[1] ? Number(m[1]) : 1;
    if (Number.isFinite(n) && n > max) max = n;
  }
  return `New project ${max + 1}`;
}

/** Show "New project 4" even if stored as "New project #4". */
export function displayProjectTitle(title: string): string {
  return title.replace(/^(new project) #(\d+)$/i, "$1 $2");
}
