// About-frame isolation for the Projects chat thread: "Show only this"
// filters to one focus (a node, or a day of changes); leaving isolation
// restores scroll. A node's frame follows its id, not its label, and is
// headed by the node's current name, so a rename does not split it
// (docs/05-decisions.md #71).
// Framing (About "…") and filter live here — message rows in messageRow.ts.

// Contents
//  1. Types
//      - IsolateChat
//      - IsolateChatOptions
//  2. Helpers
//      - frameOf()
//  3. Public API
//      - createIsolateChat()

import { changesDayName } from "./focusPath.js";
import { messageRow } from "./messageRow.js";
import type { ChatMessage } from "../../dataShapes.js";

// 1. Types

export type IsolateChat = {
  /** Drop isolation (full thread again). */
  clear: () => void;
  /** Render thread into `threadEl`, applying isolation if set. */
  fill: (
    messages: ChatMessage[],
    onFocusClick?: (stepId: string, label: string) => void,
    onDayClick?: (day: string) => void,
  ) => void;
};

export type IsolateChatOptions = {
  threadEl: HTMLDivElement;
  /** Map a focus label to a step id when history omitted focus_step_id. */
  resolveStepId?: (label: string) => string | null;
  /** A node's current label from the map, or null if it is gone. */
  labelForStepId?: (stepId: string) => string | null;
  /** Re-render the workspace after isolate / show-full. */
  onChange: () => void;
};

// 2. Helpers

type Frame = { key: string; name: string; day: string | null };

/** What a message's About-frame is: its node (by id when saved, else by
 * label), or its day of changes. `key` groups messages; `name` is shown:
 * the node's current label when the map still has it. */
function frameOf(
  message: ChatMessage,
  labelForStepId?: (stepId: string) => string | null,
): Frame | null {
  const focus = message.focus?.trim();
  const stepId = message.focus_step_id?.trim();
  if (stepId) {
    const name = labelForStepId?.(stepId) || focus || stepId;
    return { key: `id:${stepId}`, name, day: null };
  }
  if (focus) return { key: focus, name: focus, day: null };
  const day = message.focus_day?.trim();
  if (day) return { key: `day:${day}`, name: changesDayName(day), day };
  return null;
}

// 3. Public API

export function createIsolateChat(options: IsolateChatOptions): IsolateChat {
  const { threadEl, resolveStepId, labelForStepId, onChange } = options;
  const frameFor = (message: ChatMessage): Frame | null =>
    frameOf(message, labelForStepId);
  let isolatedFocus: Frame | null = null;
  let preIsolationScrollTop: number | null = null;

  function isolationBanner(): HTMLDivElement {
    const banner = document.createElement("div");
    banner.className = "thread-isolation-banner";
    const label = document.createElement("span");
    label.textContent = `Showing only: About “${isolatedFocus?.name}”`;
    const back = document.createElement("button");
    back.type = "button";
    back.className = "thread-isolation-back";
    back.textContent = "← Show full conversation";
    back.addEventListener("click", () => {
      isolatedFocus = null;
      onChange();
    });
    banner.append(label, back);
    return banner;
  }

  function fill(
    messages: ChatMessage[],
    onFocusClick?: (stepId: string, label: string) => void,
    onDayClick?: (day: string) => void,
  ): void {
    threadEl.innerHTML = "";

    if (isolatedFocus) {
      threadEl.appendChild(isolationBanner());
      for (const message of messages) {
        if (frameFor(message)?.key !== isolatedFocus.key) continue;
        threadEl.appendChild(messageRow(message));
      }
      threadEl.scrollTop = threadEl.scrollHeight;
      return;
    }

    let section: HTMLDivElement | null = null;
    let sectionKey: string | null = null;

    for (const message of messages) {
      const current = frameFor(message);
      const focus = current && !current.day ? current.name : null;
      if ((current?.key ?? null) !== sectionKey) {
        sectionKey = current?.key ?? null;
        if (current) {
          const frame = document.createElement("div");
          frame.className = "chat-focus-section";
          const stepId = message.focus_step_id?.trim();
          if (focus) frame.dataset.focusLabel = focus;
          if (stepId) frame.dataset.focusStepId = stepId;
          if (current.day && onDayClick) {
            const day = current.day;
            frame.classList.add("is-clickable");
            frame.title = `Talk about ${current.name} again`;
            frame.addEventListener("click", () => onDayClick(day));
          } else if (focus && onFocusClick) {
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
          marker.textContent = `About “${current.name}”`;
          const isolateBtn = document.createElement("button");
          isolateBtn.type = "button";
          isolateBtn.className = "thread-isolate-button";
          isolateBtn.textContent = "Show only this →";
          isolateBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            preIsolationScrollTop = threadEl.scrollTop;
            isolatedFocus = current;
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
      preIsolationScrollTop = null;
    },
    fill,
  };
}
