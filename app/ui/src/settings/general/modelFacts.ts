// General — Settings → General page body.
//
// Shape: ../register/blocks.ts

import { fetchModel } from "../../api.js";
import { arrangeStack, modelBlock } from "../register/index.js";

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

/** Fill a `.settings-register` host with model facts via register blocks. */
export async function mountModelFacts(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const error = el("p", "error");
  error.hidden = true;
  host.appendChild(error);

  try {
    const info = await fetchModel();
    host.appendChild(
      arrangeStack([
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
