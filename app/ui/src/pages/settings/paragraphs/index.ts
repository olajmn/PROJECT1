// Settings paragraph system — shared by General, Directory, Logs.
//
//   types.ts      — Para / Block / Group
//   templates.ts  — title | meta | fact | empty
//   layout.ts     — block / stack / group
//   ageClock.ts   — live Created/Started age
//
// Styles: css/pages/settings/paragraphs.css
// Edit shape per tab in that tab's spec.ts.

export type {
  Block,
  EmptyPara,
  FactPara,
  Group,
  MetaPara,
  Para,
  TitlePara,
} from "./types.js";

export { renderPara } from "./templates.js";
export { renderBlock, renderGroup, renderStack } from "./layout.js";
export { startAgeClock } from "./ageClock.js";
