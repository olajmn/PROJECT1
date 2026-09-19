// Log — one page for looking back: Completed, History, Sessions.
// Primary work stays on Projects; Vision stays its own page.
// Tab from ?tab= / #hash so old completed/history/sessions URLs can land here.

// Contents
//  1. Tabs
//  2. Completed
//  3. History
//  4. Sessions
//  5. Initialization

import {
  fetchCompletedGoals,
  fetchHistory,
  fetchSessions,
} from "../api.js";
import { initVisionCount } from "../visionCount.js";
import { planElement } from "../map/tree.js";
import type {
  GoalView,
  HistoryEntry,
  SessionGoalEvent,
  SessionLogView,
  SessionVisionEvent,
} from "../types.js";

type PanelId = "completed" | "history" | "sessions";

const PANELS: PanelId[] = ["completed", "history", "sessions"];

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

const loaded: Record<PanelId, boolean> = {
  completed: false,
  history: false,
  sessions: false,
};

// 1. Tabs

function resolveInitialPanel(): PanelId {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("tab");
  const fromHash = window.location.hash.replace(/^#/, "");
  const raw = (fromQuery || fromHash || "completed").toLowerCase();
  return PANELS.includes(raw as PanelId) ? (raw as PanelId) : "completed";
}

function showPanel(id: PanelId): void {
  for (const panel of PANELS) {
    const section = document.getElementById(`panel-${panel}`);
    const tab = document.querySelector<HTMLButtonElement>(
      `.log-tabs [data-panel="${panel}"]`,
    );
    const on = panel === id;
    if (section) section.hidden = !on;
    if (tab) tab.setAttribute("aria-selected", on ? "true" : "false");
  }
  const url = new URL(window.location.href);
  url.searchParams.set("tab", id);
  url.hash = "";
  history.replaceState(null, "", url.toString());
  void loadPanel(id);
}

function wireTabs(): void {
  const tabs = Array.from(
    document.querySelectorAll<HTMLButtonElement>(".log-tabs [data-panel]"),
  );
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      const id = tab.dataset.panel as PanelId;
      if (PANELS.includes(id)) showPanel(id);
    });
  }
}

async function loadPanel(id: PanelId): Promise<void> {
  if (loaded[id]) return;
  try {
    if (id === "completed") await loadCompleted();
    else if (id === "history") await loadHistory();
    else await loadSessions();
    loaded[id] = true;
  } catch (err) {
    const empty = document.getElementById(`empty-${id}`);
    if (empty) {
      empty.hidden = false;
      empty.textContent = `(error: ${(err as Error).message})`;
    }
  }
}

// 2. Completed

function renderGoalCard(goal: GoalView): HTMLElement {
  const card = document.createElement("article");
  card.className = "goal-card";

  const header = document.createElement("div");
  header.className = "card-header";
  const title = document.createElement("h2");
  title.textContent = goal.goal;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${goal.goal_id}`;
  header.append(title, id);
  card.appendChild(header);

  if (goal.surface) {
    const surface = document.createElement("p");
    surface.className = "surface";
    surface.textContent = goal.surface;
    card.appendChild(surface);
  }

  if (goal.node) {
    card.appendChild(planElement(goal.node));
  }

  return card;
}

async function loadCompleted(): Promise<void> {
  const list = document.getElementById("goal-list") as HTMLDivElement;
  const empty = document.getElementById("empty-completed") as HTMLParagraphElement;
  const goals = await fetchCompletedGoals();
  list.innerHTML = "";
  empty.hidden = goals.length > 0;
  for (const goal of goals) {
    list.appendChild(renderGoalCard(goal));
  }
}

// 3. History

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

async function loadHistory(): Promise<void> {
  const list = document.getElementById("history-list") as HTMLDivElement;
  const empty = document.getElementById("empty-history") as HTMLParagraphElement;
  const entries = await fetchHistory();
  list.innerHTML = "";
  empty.hidden = entries.length > 0;
  for (const entry of entries) {
    list.appendChild(renderEntry(entry));
  }
}

// 4. Sessions

interface TimelineEntry {
  created_at: string;
  label: string;
  text: string;
}

function goalTimelineEntry(event: SessionGoalEvent): TimelineEntry {
  return {
    created_at: event.created_at,
    label: event.feedback === null ? "goal created" : "feedback",
    text:
      event.feedback === null
        ? `${event.goal} (#${event.goal_id})`
        : `#${event.goal_id}: ${event.feedback}`,
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
  const list = document.getElementById("session-list") as HTMLDivElement;
  const empty = document.getElementById("empty-sessions") as HTMLParagraphElement;
  const sessions = await fetchSessions();
  list.innerHTML = "";
  empty.hidden = sessions.length > 0;
  for (const session of sessions) {
    list.appendChild(renderSession(session));
  }
}

// 5. Initialization

wireTabs();
showPanel(resolveInitialPanel());
initVisionCount();
