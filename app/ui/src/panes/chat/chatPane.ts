// Fills the chat column for one project: Status panel and message thread.
//
// Selection state stays in index.ts. This pane only draws the column and
// calls back when a Status node name or an About-frame should select a map
// node, or a Status day should select that day's changes.
//
// Contents
//  1. Types
//      - ChatPane
//  2. Public API
//      - installChatPane()

import type { ProjectView } from "../../dataShapes.js";
import { createIsolateChat } from "./showOnlyThis.js";
import { createStatusPanel } from "./statusPanel/statusPanel.js";

// 1. Types

export type ChatPane = {
  /** No project (or Create open): clear Status and show a placeholder. */
  fillEmpty: (placeholder: string) => void;
  /** One open project: Status + thread. */
  fillProject: (opts: {
    project: ProjectView;
    onSelectNode: (stepId: string, label: string) => void;
    resolveStepId: (label: string) => string | null;
    selectedDay: string | null;
    onSelectDay: (day: string | null) => void;
  }) => void;
  clearIsolate: () => void;
  readonly threadEl: HTMLDivElement;
};

type ChatPaneOpts = {
  statusPanel: HTMLElement;
  statusResize: HTMLElement;
  statusToggle: HTMLButtonElement;
  threadEl: HTMLDivElement;
  /** Re-render the shell when isolate filter changes. */
  onIsolateChange: () => void;
};

// 2. Public API

export function installChatPane(opts: ChatPaneOpts): ChatPane {
  const statusPanel = createStatusPanel(
    opts.statusPanel,
    opts.statusResize,
    opts.statusToggle,
  );

  let resolveStepIdLive: ((label: string) => string | null) | null = null;

  const isolateChat = createIsolateChat({
    threadEl: opts.threadEl,
    resolveStepId: (label) => resolveStepIdLive?.(label) ?? null,
    onChange: opts.onIsolateChange,
  });

  const fillPlaceholder = (text: string): void => {
    opts.threadEl.innerHTML = "";
    const note = document.createElement("p");
    note.className = "chat-placeholder";
    note.textContent = text;
    opts.threadEl.appendChild(note);
  };

  return {
    threadEl: opts.threadEl,
    clearIsolate: () => isolateChat.clear(),
    fillEmpty: (placeholder) => {
      resolveStepIdLive = null;
      fillPlaceholder(placeholder);
      statusPanel.fill(null, () => {});
    },
    fillProject: ({ project, onSelectNode, resolveStepId, selectedDay, onSelectDay }) => {
      resolveStepIdLive = resolveStepId;
      isolateChat.fill(
        project.thread ?? [],
        (stepId, label) => onSelectNode(stepId, label),
        (day) => onSelectDay(day),
      );
      statusPanel.fill(
        project.status,
        (label) => {
          const stepId = resolveStepId(label);
          if (!stepId) return;
          onSelectNode(stepId, label);
        },
        selectedDay,
        onSelectDay,
      );
    },
  };
}
