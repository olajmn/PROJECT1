// The Sessions page - one card per persisted Session (data_persistence.
// start_session(), one per real run of cli.py's main() or server.py),
// each showing when it started, whether it's still open, and a
// derived timeline of what happened during it (goals created/replanned,
// visions created) - reconstructed at read time from History/Visions'
// own timestamps (GET /api/sessions, server.py's _session_log_view()),
// not a separate activity log written by every action. `ended_at` is
// always null today (no graceful-shutdown hook exists yet), so every
// Session here - including ones from a previous, no-longer-running
// process - renders as still open; a known limitation, not a bug (see
// docs/04-current-state.md § 5).

import { fetchSessions } from "./api.js";
import { initNavCounts } from "./nav.js";
import type { SessionGoalEvent, SessionLogView, SessionVisionEvent } from "./types.js";

const list = document.getElementById("session-list") as HTMLDivElement;
const empty = document.getElementById("empty") as HTMLParagraphElement;

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

// One shared timeline shape for rendering - goal and Vision events
// otherwise have different fields, but both reduce to "when, and what
// to call it" for display purposes.
interface TimelineEntry {
  created_at: string;
  label: string;
  text: string;
}

function goalTimelineEntry(event: SessionGoalEvent): TimelineEntry {
  return {
    created_at: event.created_at,
    label: event.feedback === null ? "goal created" : "feedback",
    text: event.feedback === null ? `${event.goal} (#${event.goal_id})` : `#${event.goal_id}: ${event.feedback}`,
  };
}

function visionTimelineEntry(event: SessionVisionEvent): TimelineEntry {
  return {
    created_at: event.created_at,
    label: "vision created",
    text: `${event.text} (#${event.vision_id})`,
  };
}

function renderSession(session: SessionLogView): HTMLElement {
  const card = document.createElement("article");
  card.className = "history-entry";

  const header = document.createElement("div");
  header.className = "card-header";
  const title = document.createElement("h2");
  title.textContent = `Session #${session.id}`;
  header.appendChild(title);
  card.appendChild(header);

  addLine(card, "started_at", session.started_at);
  addLine(card, "status", session.ended_at ?? "(ongoing)");

  const timeline = [
    ...session.goal_events.map(goalTimelineEntry),
    ...session.vision_events.map(visionTimelineEntry),
  ].sort((a, b) => a.created_at.localeCompare(b.created_at));

  if (timeline.length === 0) {
    const emptyState = document.createElement("p");
    emptyState.className = "empty-state";
    emptyState.textContent = "(nothing happened in this session yet)";
    card.appendChild(emptyState);
  } else {
    for (const entry of timeline) {
      addLine(card, entry.label, `${entry.text} - ${entry.created_at}`);
    }
  }

  return card;
}

async function loadSessions(): Promise<void> {
  const sessions = await fetchSessions();
  list.innerHTML = "";
  empty.hidden = sessions.length > 0;
  for (const session of sessions) {
    list.appendChild(renderSession(session));
  }
}

loadSessions().catch((err) => {
  empty.hidden = false;
  empty.textContent = `(error loading sessions: ${(err as Error).message})`;
});
initNavCounts();
