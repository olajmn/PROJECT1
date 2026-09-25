// Fills the chat column for one project: Status panel, message thread,
// and the Print map button.
//
// Selection state stays in index.ts. This pane only draws the column and
// calls back when a Status node name or an About-frame should select a map
// node.
//
// Contents
//  1. Types
//      - ChatPane
//  2. Public API
//      - installChatPane()

import type { ProjectView } from "../../dataShapes.js";
import { messageRow } from "./messageRow.js";
import { printMapText } from "./printMap.js";
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
  }) => void;
  clearIsolate: () => void;
  updatePrintButton: (
    hasProject: boolean,
    selectedNodeId: string | null,
  ) => void;
  readonly threadEl: HTMLDivElement;
};

type ChatPaneOpts = {
  statusPanel: HTMLElement;
  statusResize: HTMLElement;
  statusToggle: HTMLButtonElement;
  threadEl: HTMLDivElement;
  printBtn: HTMLButtonElement;
  /** Re-render the shell when isolate filter changes. */
  onIsolateChange: () => void;
  getProject: () => ProjectView | null;
  getSelectedNodeId: () => string | null;
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

  opts.printBtn.addEventListener("click", () => {
    const project = opts.getProject();
    if (!project) return;
    const text = printMapText(project.node, opts.getSelectedNodeId());
    opts.threadEl.append(messageRow({ role: "agent", text }));
    opts.threadEl.scrollTop = opts.threadEl.scrollHeight;
  });

  return {
    threadEl: opts.threadEl,
    clearIsolate: () => isolateChat.clear(),
    fillEmpty: (placeholder) => {
      resolveStepIdLive = null;
      fillPlaceholder(placeholder);
      statusPanel.fill(null, () => {});
    },
    fillProject: ({ project, onSelectNode, resolveStepId }) => {
      resolveStepIdLive = resolveStepId;
      isolateChat.fill(project.thread ?? [], (stepId, label) => {
        onSelectNode(stepId, label);
      });
      statusPanel.fill(project.status, (label) => {
        const stepId = resolveStepId(label);
        if (!stepId) return;
        onSelectNode(stepId, label);
      });
    },
    updatePrintButton: (hasProject, selectedNodeId) => {
      opts.printBtn.disabled = !hasProject;
      if (selectedNodeId) {
        opts.printBtn.textContent = "Print path";
        opts.printBtn.title = "Print this node's path as stored on the map";
      } else {
        opts.printBtn.textContent = "Print map";
        opts.printBtn.title = "Print the stored map labels";
      }
    },
  };
}
