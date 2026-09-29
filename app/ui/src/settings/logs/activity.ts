// Logs — Settings → Logs, All activity: every saved change across
// projects, newest first, in day sections (logList.ts), one page at a
// time with "Show more" at the bottom. One project's tape:
// projectTimeline.ts.

import { fetchLog } from "../../api.js";
import type { LogEntry } from "../../dataShapes.js";
import { settingsAction, settingsError, settingsHint } from "../rows.js";
import { logDaySections } from "./logList.js";

// Entries per page — the same number as LOG_LIMIT in
// backend/api/activity_log.py. A full page means there may be more.
const LOG_PAGE = 200;

/** Fill `#logs` with the activity log. */
export async function mountLogs(host: HTMLElement): Promise<void> {
  const entries: LogEntry[] = [];

  const more = settingsAction("Show more", (btn) => void loadPage(btn));
  more.classList.add("settings-more");

  // Every page redraws all loaded entries, so a day that spans two pages
  // stays one section.
  const loadPage = async (btn?: HTMLButtonElement): Promise<void> => {
    if (btn) btn.disabled = true;
    try {
      const page = await fetchLog(entries.length);
      entries.push(...page);
      if (entries.length === 0) {
        host.replaceChildren(settingsHint("Nothing has happened yet."));
        return;
      }
      host.replaceChildren(...logDaySections(entries, true));
      if (page.length >= LOG_PAGE) host.appendChild(more);
    } catch (err) {
      host.appendChild(settingsError((err as Error).message));
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  await loadPage();
}
