// About-frame isolation for the Projects chat thread: "Show only this"
// filters to one focus label; leaving isolation restores scroll.
// Framing (About "…") and filter live here — message rows in messageRow.ts.

// Contents
//  1. Types
//      - IsolateChat
//      - IsolateChatOptions
//  2. Public API
//      - createIsolateChat()

import { messageRow } from "./messageRow.js";
import type { ChatMessage } from "../../dataShapes.js";

// 1. Types

export type IsolateChat = {
  /** Drop isolation (full thread again). */
  clear: () => void;
  /** Show only one About-stretch (talk-tree node). */
  isolateRange: (start: number, end: number, label: string) => void;
  /** Render thread into `threadEl`, applying isolation if set. */
  fill: (
    messages: ChatMessage[],
    onFocusClick?: (stepId: string, label: string) => void,
  ) => void;
};

export type IsolateChatOptions = {
  threadEl: HTMLDivElement;
  /** Map a focus label to a step id when history omitted focus_step_id. */
  resolveStepId?: (label: string) => string | null;
  /** Re-render the workspace after isolate / show-full. */
  onChange: () => void;
};

// 2. Public API

export function createIsolateChat(options: IsolateChatOptions): IsolateChat {
  const { threadEl, resolveStepId, onChange } = options;
  let isolatedFocus: string | null = null;
  let isolatedRange: { start: number; end: number; label: string } | null =
    null;
  let preIsolationScrollTop: number | null = null;

  function isolationBanner(): HTMLDivElement {
    const banner = document.createElement("div");
    banner.className = "thread-isolation-banner";
    const label = document.createElement("span");
    const shown = isolatedRange?.label ?? isolatedFocus;
    label.textContent = `Showing only: About “${shown}”`;
    const back = document.createElement("button");
    back.type = "button";
    back.className = "thread-isolation-back";
    back.textContent = "← Show full conversation";
    back.addEventListener("click", () => {
      isolatedFocus = null;
      isolatedRange = null;
      onChange();
    });
    banner.append(label, back);
    return banner;
  }

  function fill(
    messages: ChatMessage[],
    onFocusClick?: (stepId: string, label: string) => void,
  ): void {
    threadEl.innerHTML = "";

    if (isolatedRange) {
      threadEl.appendChild(isolationBanner());
      for (const message of messages.slice(
        isolatedRange.start,
        isolatedRange.end,
      )) {
        threadEl.appendChild(messageRow(message));
      }
      threadEl.scrollTop = threadEl.scrollHeight;
      return;
    }

    if (isolatedFocus) {
      threadEl.appendChild(isolationBanner());
      for (const message of messages) {
        if ((message.focus?.trim() || null) !== isolatedFocus) continue;
        threadEl.appendChild(messageRow(message));
      }
      threadEl.scrollTop = threadEl.scrollHeight;
      return;
    }

    let section: HTMLDivElement | null = null;
    let sectionFocus: string | null = null;

    for (const message of messages) {
      const focus = message.focus?.trim() || null;
      if (focus !== sectionFocus) {
        sectionFocus = focus;
        if (focus) {
          const frame = document.createElement("div");
          frame.className = "chat-focus-section";
          frame.dataset.focusLabel = focus;
          const stepId = message.focus_step_id?.trim();
          if (stepId) frame.dataset.focusStepId = stepId;
          if (onFocusClick) {
            frame.classList.add("is-clickable");
            frame.title = `Select “${focus}” on the map`;
            frame.addEventListener("click", () => {
              const label = frame.dataset.focusLabel || focus;
              const id =
                frame.dataset.focusStepId ||
                resolveStepId?.(label) ||
                null;
              if (id) onFocusClick(id, label);
            });
          }
          const header = document.createElement("div");
          header.className = "chat-focus-header";
          const marker = document.createElement("span");
          marker.className = "chat-focus-marker";
          marker.textContent = `About “${focus}”`;
          const isolateBtn = document.createElement("button");
          isolateBtn.type = "button";
          isolateBtn.className = "thread-isolate-button";
          isolateBtn.textContent = "Show only this →";
          isolateBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            preIsolationScrollTop = threadEl.scrollTop;
            isolatedFocus = focus;
            isolatedRange = null;
            onChange();
          });
          header.append(marker, isolateBtn);
          frame.appendChild(header);
          threadEl.appendChild(frame);
          section = frame;
        } else {
          section = null;
        }
      } else if (
        focus &&
        section &&
        message.focus_step_id &&
        !section.dataset.focusStepId
      ) {
        section.dataset.focusStepId = message.focus_step_id.trim();
      }
      (section ?? threadEl).appendChild(messageRow(message));
    }
    if (preIsolationScrollTop !== null) {
      threadEl.scrollTop = preIsolationScrollTop;
      preIsolationScrollTop = null;
    } else {
      threadEl.scrollTop = threadEl.scrollHeight;
    }
  }

  return {
    clear: () => {
      isolatedFocus = null;
      isolatedRange = null;
      preIsolationScrollTop = null;
    },
    isolateRange: (start, end, label) => {
      isolatedFocus = null;
      preIsolationScrollTop = threadEl.scrollTop;
      isolatedRange = { start, end, label };
    },
    fill,
  };
}
