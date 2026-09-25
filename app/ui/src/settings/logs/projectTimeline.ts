// One project's full timeline — every saved change, oldest first,
// ungrouped. Settings → Logs project scope. Status compresses the same
// events; this is the raw tape for inspection.

import { fetchProjectTimeline } from "../../api.js";
import type { LogEntry } from "../../dataShapes.js";
import {
  arrangeStack,
  logBlock,
  startAgeClock,
} from "../paragraphs/index.js";
import { el } from "../paragraphs/makeTag.js";

function tapeBlock(entry: LogEntry) {
  // Event name as title (node_added, chat, …); kind as secondary label.
  return logBlock({
    kind: entry.event,
    project: entry.kind,
    at: entry.at,
    text: entry.text,
    focus: entry.focus,
  });
}

/** Fill a `.settings-register` host with one project's ungrouped timeline. */
export async function mountProjectTimeline(
  host: HTMLElement,
  projectId: number,
): Promise<void> {
  host.replaceChildren();

  const empty = el("p", "empty-state", "No saved changes for this project.");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(empty, error);

  try {
    const entries = await fetchProjectTimeline(projectId);
    empty.hidden = entries.length > 0;
    if (entries.length === 0) return;

    host.appendChild(arrangeStack(entries.map(tapeBlock)));
    startAgeClock(host);
  } catch (err) {
    error.hidden = false;
    error.textContent = `(error: ${(err as Error).message})`;
  }
}
