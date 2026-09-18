// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

// Contents
//  1. Free conversation
//      - sendMessage()
//  2. Goals
//      - fetchActiveGoals()
//      - createGoal()
//      - sendGoalFeedback()
//      - cancelGoal()
//      - setGoalVision()
//      - fetchCompletedGoals()
//  3. History
//      - fetchHistory()
//  4. Vision
//      - fetchVisions()
//      - createVision()
//      - archiveVision()
//  5. Chat focus
//      - fetchChatFocus()
//      - setChatFocus()
//  6. Sessions
//      - fetchSessions()
//  7. Steps (scratch tree)
//      - fetchTree()
//      - createTree()
//      - zoomStep()

import type { AgentResponse, ChatFocusView, GoalView, HistoryEntry, SessionLogView, TreeView, VisionView } from "./types.js";

// 1. Free conversation

export async function sendMessage(text: string): Promise<AgentResponse> {
  const res = await fetch("/api/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as AgentResponse;
}

// 2. Goals

export async function fetchActiveGoals(): Promise<GoalView[]> {
  const res = await fetch("/api/goals");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView[];
}

export async function createGoal(text: string): Promise<GoalView> {
  const res = await fetch("/api/goals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function sendGoalFeedback(
  goalId: number,
  text: string,
  focusLabel?: string | null,
  focusStepId?: string | null,
): Promise<GoalView> {
  const body: {
    text: string;
    focus_label?: string;
    focus_step_id?: string;
  } = { text };
  if (focusLabel) {
    body.focus_label = focusLabel;
  }
  if (focusStepId) {
    body.focus_step_id = focusStepId;
  }
  const res = await fetch(`/api/goals/${goalId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function cancelGoal(goalId: number): Promise<GoalView> {
  const res = await fetch(`/api/goals/${goalId}/cancel`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function setGoalVision(goalId: number, visionId: number | null): Promise<GoalView> {
  const res = await fetch(`/api/goals/${goalId}/vision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vision_id: visionId }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function zoomGoalStep(goalId: number, stepId: string): Promise<GoalView> {
  const res = await fetch(`/api/goals/${goalId}/zoom/${stepId}`, { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    // send_error() returns an HTML page; pull the plain reason if present.
    const plain = detail.match(/no timeframe[\s\S]*?(?=<|$)/i)?.[0]
      ?? detail.match(/Error code: (\d+)[\s\S]*?<p>([^<]+)/i)?.[2]
      ?? detail.match(/cannot zoom[^.<]*/i)?.[0];
    throw new Error((plain || detail || `request failed: ${res.status}`).slice(0, 200));
  }
  return (await res.json()) as GoalView;
}

export async function addProgressionStep(
  goalId: number,
  label: string,
  parentId?: string | null,
): Promise<GoalView> {
  const body: { label: string; parent_id?: string } = { label };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/goals/${goalId}/progression`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function removeProgressionStep(goalId: number, stepId: string): Promise<GoalView> {
  const res = await fetch(`/api/goals/${goalId}/progression/${stepId}/remove`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView;
}

export async function fetchCompletedGoals(): Promise<GoalView[]> {
  const res = await fetch("/api/goals/completed");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView[];
}

// 3. History

export async function fetchHistory(): Promise<HistoryEntry[]> {
  const res = await fetch("/api/history");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as HistoryEntry[];
}

// 4. Vision

export async function fetchVisions(): Promise<VisionView[]> {
  const res = await fetch("/api/visions");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as VisionView[];
}

export async function createVision(text: string): Promise<VisionView> {
  const res = await fetch("/api/visions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as VisionView;
}

export async function archiveVision(visionId: number): Promise<VisionView> {
  const res = await fetch(`/api/visions/${visionId}/archive`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as VisionView;
}

// 5. Chat focus

export async function fetchChatFocus(): Promise<ChatFocusView> {
  const res = await fetch("/api/chat-focus");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ChatFocusView;
}

export async function setChatFocus(goalId: number | null): Promise<ChatFocusView> {
  const res = await fetch("/api/chat-focus", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal_id: goalId }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ChatFocusView;
}

// 6. Sessions

export async function fetchSessions(): Promise<SessionLogView[]> {
  const res = await fetch("/api/sessions");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionLogView[];
}

// 7. Steps (scratch tree)

/** Whatever tree the server currently holds - `root` is null if none
 * has been built yet, or if the process restarted (it is in memory
 * only). */
export async function fetchTree(): Promise<TreeView> {
  const res = await fetch("/api/tree");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as TreeView;
}

/** Unlike the wrappers above, these surface the server's own reason
 * phrase instead of just the status code - the Steps routes reject
 * text with no timeframe in it (422), and that reason is the whole
 * point of the rejection, not an internal detail. */
async function postTree(path: string, body?: unknown): Promise<TreeView> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(res.statusText || `request failed: ${res.status}`);
  }
  return (await res.json()) as TreeView;
}

export function createTree(text: string): Promise<TreeView> {
  return postTree("/api/tree", { text });
}

export function zoomStep(stepId: string): Promise<TreeView> {
  return postTree(`/api/tree/${stepId}/zoom`);
}
