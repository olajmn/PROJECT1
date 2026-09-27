// The Send form: sends a chat message, or — when a node is selected and
// the text has several lines — adds that text as nodes under it.
//
// Contents
//  1. Public API
//      - installSendMessage()

import { pasteText, sendChatMessage } from "../../api.js";
import type { ProjectView } from "../../dataShapes.js";
import { setButtonBusy } from "../../shell/busyButton.js";

type SendMessageOpts = {
  form: HTMLFormElement;
  input: HTMLTextAreaElement;
  errorEl: HTMLParagraphElement;
  getProject: () => ProjectView | null;
  getSelectedNodeId: () => string | null;
  getSelectedNodeLabel: () => string | null;
  getSelectedDay: () => string | null;
  onUpdated: (updated: ProjectView) => void;
};

// 1. Public API

export function installSendMessage(opts: SendMessageOpts): void {
  opts.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const project = opts.getProject();
    if (!project) return;
    const text = opts.input.value.trim();
    if (!text) return;
    const sendButton = opts.form.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    const selectedNodeId = opts.getSelectedNodeId();
    const selectedNodeLabel = opts.getSelectedNodeLabel();
    const selectedDay = opts.getSelectedDay();
    opts.input.disabled = true;
    setButtonBusy(sendButton, true);
    opts.errorEl.hidden = true;
    try {
      // A multi-line paste while focused on a node is imported as
      // children of that node instead of sent as an ordinary chat
      // message - only on Send, not on paste itself (a paste is just
      // text arriving in the compose box, same as typing it; it should
      // not act on its own before the user chooses to send it). Falls
      // back to an ordinary message if nothing recognizable parses out.
      // unwrap=false (keep everything) - unlike the Paste structure
      // form, chat has no preview to catch a wrong guess before it
      // happens, so the safe default is an extra node the user can
      // remove afterward (visible, reversible), never a silently
      // discarded one they never see.
      let updated: ProjectView;
      if (selectedNodeId && text.includes("\n")) {
        try {
          updated = await pasteText(
            project.project_id,
            text,
            selectedNodeId,
            false,
          );
        } catch {
          updated = await sendChatMessage(
            project.project_id,
            text,
            selectedNodeLabel,
            selectedNodeId,
          );
        }
      } else {
        updated = await sendChatMessage(
          project.project_id,
          text,
          selectedNodeLabel,
          selectedNodeId,
          selectedDay,
        );
      }
      opts.input.value = "";
      opts.input.dispatchEvent(new Event("input"));
      opts.onUpdated(updated);
    } catch (err) {
      opts.errorEl.hidden = false;
      opts.errorEl.textContent = `(error: ${(err as Error).message})`;
    } finally {
      opts.input.disabled = false;
      setButtonBusy(sendButton, false);
    }
  });
}
