// Line / block / group shapes for the Settings register UI.
//
// Primitive for metadata: fact = { label, value }.
// Optional `created` on a fact turns the value into stamp · live age.
// Title is the block hero; empty is a muted placeholder line.

export type TitleLine = {
  t: "title";
  kind: string;
  name: string;
};

/** Label → value row. The general metadata primitive. */
export type FactLine = {
  t: "fact";
  label: string;
  /** Static text. Omit when using `created`. */
  value?: string;
  /** ISO timestamp; value becomes stamp · live age. */
  created?: string | null;
};

export type EmptyLine = {
  t: "empty";
  text: string;
};

/** One visual line. Change `t` to switch paintLine. */
export type Line = TitleLine | FactLine | EmptyLine;

/** Vertical stack of lines. */
export type Block = Line[];

/** Two-column group (Id | projects). */
export type Group = {
  active?: boolean;
  dataSimUserId?: string;
  left: Block;
  right: Block[];
};
