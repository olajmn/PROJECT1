// How many levels a map opens with in the public demo (docs/demo.md), set
// once at startup from GET /api/session. null outside the demo: the map
// then picks a depth that fits the whole tree on screen.

let startDepth: number | null = null;

export function setMapStartDepth(depth: number | null): void {
  startDepth = depth;
}

export function mapStartDepth(): number | null {
  return startDepth;
}
