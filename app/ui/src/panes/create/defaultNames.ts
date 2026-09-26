/**
 * Display of default names. The names themselves ("New project N") are
 * picked server side — `next_default_name()` in
 * backend/project/panes/create/lifecycle.py.
 */

/** Show "New project 4" even if stored as "New project #4". */
export function displayProjectTitle(title: string): string {
  return title.replace(/^(new project) #(\d+)$/i, "$1 $2");
}
