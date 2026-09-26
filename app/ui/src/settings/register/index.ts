// Settings register UI — shared by General, Directory, Logs.
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
  idGroup,
  logBlock,
  modelBlock,
  orphanGroup,
  projectBlock,
  type IdValues,
  type LogValues,
  type ModelValues,
  type ProjectValues,
} from "./blocks.js";

export { paintLine } from "./paintLine.js";
export { arrangeBlock, arrangeGroup, arrangeStack } from "./layout.js";
export { startAgeClock } from "./ageClock.js";
export { el } from "./dom.js";
