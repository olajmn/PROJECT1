// Logs — Settings → Logs page body.
//
// Shape: ../paragraphs/registerTemplate.ts

import { fetchSessions } from "../../../api.js";
import {
  arrangeStack,
  sessionBlock,
  startAgeClock,
} from "../paragraphs/index.js";

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

/** Fill a `.settings-register` host with process sessions via registerTemplate. */
export async function mountLogs(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const empty = el("p", "empty-state", "No process sessions yet.");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(empty, error);

  try {
    const sessions = await fetchSessions();
    empty.hidden = sessions.length > 0;
    if (sessions.length === 0) return;

    host.appendChild(
      arrangeStack(
        sessions.map((session, index) =>
          sessionBlock({
            id: session.id,
            startedAt: session.started_at,
            current: index === 0,
          }),
        ),
      ),
    );
    startAgeClock(host);
  } catch (err) {
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
}
