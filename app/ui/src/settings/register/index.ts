// Settings register UI — shared by Directory and Logs (being replaced by
// ../rows.ts page by page; TODO.md § Parallel paths).
//
//   blocks.ts    — title + fact recipes; edit look here
//   types.ts     — title | fact | empty, Block, Group
//   paintLine.ts — how each line paints
//   layout.ts    — block / stack / group
//   ageClock.ts  — live age on fact.created
//   dom.ts       — tiny DOM helper
//
// Styles: css/settings/register.css

export type {
  Block,
  EmptyLine,
  FactLine,
  Group,
  Line,
  TitleLine,
} from "./types.js";

export {
  accountGroup,
  logBlock,
  orphanGroup,
  projectBlock,
  type IdValues,
  type LogValues,
  type ProjectValues,
} from "./blocks.js";

export { paintLine } from "./paintLine.js";
export { arrangeBlock, arrangeGroup, arrangeStack } from "./layout.js";
export { startAgeClock } from "./ageClock.js";
export { el } from "./dom.js";
