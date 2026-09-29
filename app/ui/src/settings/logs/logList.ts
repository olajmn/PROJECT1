// Logs as day sections of one-line rows: "Today", "Yesterday", or a date,
// then time · (project) · what happened. Shared by All activity
// (activity.ts) and one project's timeline (projectTimeline.ts).

// Contents
//  1. Day labels
//  2. logDaySections()

import type { LogEntry } from "../../dataShapes.js";
import { settingsGroup, settingsRow, settingsSection, shortDate } from "../rows.js";

// 1. Day labels

function localDayKey(when: Date): string {
  return `${when.getFullYear()}-${when.getMonth()}-${when.getDate()}`;
}

/** "Today", "Yesterday", or "28 Sep 2026" — as in Current state. */
function dayLabel(when: Date): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (localDayKey(when) === localDayKey(today)) return "Today";
  if (localDayKey(when) === localDayKey(yesterday)) return "Yesterday";
  return shortDate(when.toISOString());
}

function timeOf(when: Date): string {
  return `${String(when.getHours()).padStart(2, "0")}:${String(when.getMinutes()).padStart(2, "0")}`;
}

// 2. logDaySections()

/** One section per day, in the order the entries come. `showProject`
 *  adds the project name (All activity); a single project's timeline
 *  leaves it out. */
export function logDaySections(entries: LogEntry[], showProject: boolean): HTMLElement[] {
  const days: { label: string; rows: HTMLElement[] }[] = [];
  let lastKey = "";
  for (const entry of entries) {
    const when = entry.at ? new Date(entry.at) : null;
    const valid = when && !Number.isNaN(when.getTime()) ? when : null;
    const key = valid ? localDayKey(valid) : "unknown";
    if (key !== lastKey) {
      days.push({ label: valid ? dayLabel(valid) : "Unknown time", rows: [] });
      lastKey = key;
    }

    const what = document.createElement("span");
    const context = [showProject ? entry.project : "", entry.kind].filter(Boolean).join(" · ");
    if (context) {
      const muted = document.createElement("span");
      muted.className = "settings-muted";
      muted.textContent = `${context} · `;
      what.appendChild(muted);
    }
    what.append(entry.text || entry.event);
    if (entry.focus) {
      const focus = document.createElement("span");
      focus.className = "settings-muted";
      focus.textContent = ` · about ${entry.focus}`;
      what.appendChild(focus);
    }

    const row = settingsRow(valid ? timeOf(valid) : "—", what);
    row.classList.add("is-log");
    days[days.length - 1].rows.push(row);
  }
  return days.map((day) => settingsSection(day.label, settingsGroup(day.rows)));
}
