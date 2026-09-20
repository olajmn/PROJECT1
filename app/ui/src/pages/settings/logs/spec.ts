// Logs layout spec — edit to steer Settings → Logs.

import type { Block } from "../paragraphs/index.js";

export type SessionValues = {
  id: number;
  startedAt: string;
  current: boolean;
};

export function sessionBlock(v: SessionValues): Block {
  return [
    {
      t: "title",
      kind: "Session",
      name: String(v.id),
      badge: v.current ? "Current" : undefined,
    },
    {
      t: "meta",
      parts: [`Id ${v.id}`],
      created: v.startedAt,
      createdLabel: "Started ",
    },
  ];
}
