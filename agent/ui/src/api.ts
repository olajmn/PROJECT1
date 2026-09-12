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

import type { AgentResponse, ChatFocusView, GoalView, HistoryEntry, SessionLogView, VisionView } from "./types.js";

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

export async function sendGoalFeedback(goalId: number, text: string): Promise<GoalView> {
  const res = await fetch(`/api/goals/${goalId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
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

export async function fetchCompletedGoals(): Promise<GoalView[]> {
  const res = await fetch("/api/goals/completed");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as GoalView[];
}

export async function fetchHistory(): Promise<HistoryEntry[]> {
  const res = await fetch("/api/history");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as HistoryEntry[];
}

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

export async function fetchSessions(): Promise<SessionLogView[]> {
  const res = await fetch("/api/sessions");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionLogView[];
}
