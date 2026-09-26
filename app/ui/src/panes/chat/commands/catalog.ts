/**
 * Slash commands the chat UI can show in the `/` menu.
 * Keep in sync with backend `panes/chat/commands/` `_COMMANDS`
 * (canonical names only — aliases stay type-only).
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
];
