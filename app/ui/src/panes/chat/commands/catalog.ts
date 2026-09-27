/**
 * Slash commands the chat UI can show in the `/` menu.
 * Keep in sync with backend `panes/chat/commands/` `_COMMANDS`
 * (canonical names in the menu; aliases count for typing highlight).
 */

export type ChatCommand = {
  /** Canonical slash, e.g. `/project_summary`. */
  slash: string;
  /** One short line under the slash in the menu. */
  blurb: string;
};

export const CHAT_COMMANDS: ChatCommand[] = [
  {
    slash: "/project_summary",
    blurb: "Summarise the project from its structure",
  },
  {
    slash: "/add",
    blurb: "Add a child: /add name, or /add Parent / Child (spaces around /)",
  },
  {
    slash: "/select",
    blurb: "Focus a node: /select Name, or /select Parent / Child (spaces around /)",
  },
  {
    slash: "/id",
    blurb: "Selected node: show its id. No selection: map shows ids ↔ names",
  },
];

/** Type-only aliases — same set as backend `_ALIASES`. */
const COMMAND_ALIASES = new Set([
  "/project-summary",
  "/map_summary",
  "/map-summary",
  "/read_map",
  "/read-map",
  "/add-node",
  "/focus",
]);

const KNOWN = new Set([
  ...CHAT_COMMANDS.map((c) => c.slash),
  ...COMMAND_ALIASES,
]);

/** First token if it is a known slash-command; else null. */
export function matchCommandPrefix(
  value: string,
): { token: string; rest: string } | null {
  const m = /^(\S+)([\s\S]*)$/.exec(value);
  if (!m) return null;
  const token = m[1];
  if (!KNOWN.has(token.toLowerCase())) return null;
  return { token, rest: m[2] ?? "" };
}
