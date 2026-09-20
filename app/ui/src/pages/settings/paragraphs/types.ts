// Paragraph / block / group shapes for Settings register UI.
//
// Change `t` on a Para to switch template. Spec files fill values.

export type TitlePara = {
  t: "title";
  kind: string;
  name: string;
  badge?: string;
};

export type MetaPara = {
  t: "meta";
  /** Plain bits before the time field, e.g. "Id 1". */
  parts: string[];
  /** ISO timestamp; live age ticks beside it. */
  created?: string | null;
  /** Label before the stamp (default "Created "). */
  createdLabel?: string;
};

/** About-style key / value row (General facts). */
export type FactPara = {
  t: "fact";
  label: string;
  value: string;
};

export type EmptyPara = {
  t: "empty";
  text: string;
};

/** One visual line. */
export type Para = TitlePara | MetaPara | FactPara | EmptyPara;

/** Vertical stack of paragraphs. */
export type Block = Para[];

/** Two-column group (Directory: Id | projects). */
export type Group = {
  active?: boolean;
  dataSimUserId?: string;
  left: Block;
  right: Block[];
};
