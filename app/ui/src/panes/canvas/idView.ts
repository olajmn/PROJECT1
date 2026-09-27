// Whether the map shows node ids (p1, p12, …) instead of labels.
// Toggled by Talk `/id` with no node selected. Display only, per page
// load: nothing is saved, and the tree itself does not change.

let showIds = false;

export function mapShowsIds(): boolean {
  return showIds;
}

export function toggleMapIds(): void {
  showIds = !showIds;
}
