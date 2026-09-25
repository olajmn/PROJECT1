// Logs — Settings → Logs page body: every saved change, newest first
// (All activity scope). One-project tape: projectTimeline.ts.
// Shape: ../register/blocks.ts (logBlock)

import { fetchLog } from "../../api.js";
import {
  arrangeStack,
  el,
  logBlock,
  startAgeClock,
} from "../register/index.js";

/** Fill a `.settings-register` host with the activity log. */
export async function mountLogs(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const empty = el("p", "empty-state", "Nothing has happened yet.");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(empty, error);

  try {
    const entries = await fetchLog();
    empty.hidden = entries.length > 0;
    if (entries.length === 0) return;

    host.appendChild(
      arrangeStack(
        entries.map((entry) =>
          logBlock({
            kind: entry.kind,
            project: entry.project,
            at: entry.at,
            text: entry.text,
            focus: entry.focus,
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
