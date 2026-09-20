// General layout spec — edit to steer Settings → General.

import type { Block } from "../paragraphs/index.js";

export type ModelValues = {
  model: string;
  provider: string;
  temperature: number;
};

export function modelBlock(v: ModelValues): Block {
  return [
    { t: "title", kind: "Model", name: v.model },
    { t: "fact", label: "Provider", value: v.provider },
    { t: "fact", label: "Temperature", value: String(v.temperature) },
  ];
}
