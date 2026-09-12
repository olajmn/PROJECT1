// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

import type { AgentResponse, GoalView, HistoryEntry, SessionView, VisionView } from "./types.js";

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

export async function fetchSession(): Promise<SessionView> {
  const res = await fetch("/api/session");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionView;
}

export async function setSession(goalId: number | null): Promise<SessionView> {
  const res = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal_id: goalId }),
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionView;
}
