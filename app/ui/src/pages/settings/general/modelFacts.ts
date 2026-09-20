// General — Settings → General page body.
//
// Shape: ./spec.ts. Shared templates: ../paragraphs.ts.

import { fetchModel } from "../../../api.js";
import { renderStack } from "../paragraphs/index.js";
import { modelBlock } from "./spec.js";

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Fill a `.settings-register` host with model facts via spec.ts. */
export async function mountModelFacts(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const error = el("p", "error");
  error.hidden = true;
  host.appendChild(error);

  try {
    const info = await fetchModel();
    host.appendChild(
      renderStack([
        modelBlock({
          model: info.model,
          provider: info.provider,
          temperature: info.temperature,
        }),
      ]),
    );
  } catch (err) {
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
}
