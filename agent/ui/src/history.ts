// The History page - the raw, unfiltered log (every record ever
// saved, not just the latest per goal - see server.py's
// _history_view()/load_history()). A log to scan, not a live status:
// no plan tree here, just each record's key fields as plain text,
// same spirit as frontend-legacy/templates/_plan_entry.html's
// key:value dump.

// Contents
//  1. Field labels
//      - PLAN_FIELD_LABELS
//  2. Rendering
//      - addLine()
//      - renderEntry()
//  3. Data loading
//      - loadHistory()
//  4. Initialization

import { fetchHistory } from "./api.js";
import { initNavCounts } from "./nav.js";
import type { HistoryEntry } from "./types.js";

const list = document.getElementById("history-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

// 1. Field labels

const PLAN_FIELD_LABELS: Record<string, string> = {
  clarification: "clarification",
  suggested_action: "suggested action",
  suggested_duration: "suggested duration",
  year: "year",
  month: "month",
  week: "week",
  today: "today",
  hour: "hour",
  minute: "minute",
  now: "now",
};

// 2. Rendering

function addLine(container: HTMLElement, label: string, value: string): void {
  const line = document.createElement("div");
  line.className = "history-line";
  const key = document.createElement("span");
  key.className = "history-key";
  key.textContent = `${label}:`;
  const val = document.createElement("span");
  val.textContent = value;
  line.append(key, val);
  container.appendChild(line);
}

function renderEntry(entry: HistoryEntry): HTMLElement {
  const card = document.createElement("article");
  card.className = "history-entry";

  addLine(card, "goal_id", String(entry.goal_id));
  addLine(card, "goal", entry.goal);
  addLine(card, "created_at", entry.created_at);
  if (entry.duration) addLine(card, "duration", entry.duration);
  if (entry.feedback) addLine(card, "feedback", entry.feedback);
  for (const [key, value] of Object.entries(entry.plan)) {
    addLine(card, PLAN_FIELD_LABELS[key] ?? key, value);
  }
  if (entry.step_count > 0) addLine(card, "steps", String(entry.step_count));
  if (entry.completed) addLine(card, "status", "completed");
  if (entry.cancelled) addLine(card, "status", "cancelled");

  return card;
}

// 3. Data loading

async function loadHistory(): Promise<void> {
  const entries = await fetchHistory();
  list.innerHTML = "";
  empty.hidden = entries.length > 0;
  for (const entry of entries) {
    list.appendChild(renderEntry(entry));
  }
}

// 4. Initialization

loadHistory().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading history: ${(err as Error).message})`;
});
initNavCounts();
