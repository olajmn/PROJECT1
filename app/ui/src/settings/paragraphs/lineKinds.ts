// Paragraph / block / group shapes for Settings register UI.
//
// Primitive for metadata: fact = { label, value }.
// Optional `created` on a fact turns the value into stamp · live age.
// Title is the block hero; empty is a muted placeholder line.

export type TitlePara = {
  t: "title";
  kind: string;
  name: string;
};

/** Label → value row. The general metadata primitive. */
export type FactPara = {
  t: "fact";
  label: string;
  /** Static text. Omit when using `created`. */
  value?: string;
  /** ISO timestamp; value becomes stamp · live age. */
  created?: string | null;
};

export type EmptyPara = {
  t: "empty";
  text: string;
};

/** One visual line. Change `t` to switch drawLine. */
export type Para = TitlePara | FactPara | EmptyPara;

/** Vertical stack of paragraphs. */
export type Block = Para[];

/** Two-column group (Id | projects). */
export type Group = {
  active?: boolean;
  dataSimUserId?: string;
  left: Block;
  right: Block[];
};
