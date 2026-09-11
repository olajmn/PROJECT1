// Thin fetch wrapper around the one endpoint server.py exposes.
// Nothing here decides anything - it sends text, returns whatever
// process_turn() already decided.

import type { AgentResponse } from "./types.js";

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
