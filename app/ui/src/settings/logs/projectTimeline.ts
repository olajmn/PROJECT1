// One project's full timeline — every saved change, oldest first, in day
// sections (logList.ts). Settings → Logs project scope. Current state
// compresses the same events; this is the raw tape for inspection.

import { fetchProjectTimeline } from "../../api.js";
import { settingsError, settingsHint } from "../rows.js";
import { logDaySections } from "./logList.js";

/** Fill `#logs` with one project's timeline. */
export async function mountProjectTimeline(
  host: HTMLElement,
  projectId: number,
): Promise<void> {
  try {
    const entries = await fetchProjectTimeline(projectId);
    if (entries.length === 0) {
      host.replaceChildren(settingsHint("No saved changes for this project."));
      return;
    }
    host.replaceChildren(...logDaySections(entries, false));
  } catch (err) {
    host.replaceChildren(settingsError((err as Error).message));
  }
}
