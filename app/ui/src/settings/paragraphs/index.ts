// Settings register UI — shared by General, Directory, Logs.
//
//   registerTemplate.ts — visual recipe (title + facts); edit look here
//   lineKinds.ts        — title | fact | empty, Block, Group
//   drawLine.ts         — how each line paints
//   arrange.ts          — block / stack / group
//   liveAge.ts          — live age on fact.created
//   makeTag.ts          — tiny DOM helper
//
// Styles: css/settings/paragraphs.css

export type {
  Block,
  EmptyPara,
  FactPara,
  Group,
  Para,
  TitlePara,
} from "./lineKinds.js";

export {
  idGroup,
  logBlock,
  modelBlock,
  orphanGroup,
  projectBlock,
  type IdValues,
  type LogValues,
  type ModelValues,
  type ProjectValues,
} from "./registerTemplate.js";

export { drawLine } from "./drawLine.js";
export { arrangeBlock, arrangeGroup, arrangeStack } from "./arrange.js";
export { startAgeClock } from "./liveAge.js";
