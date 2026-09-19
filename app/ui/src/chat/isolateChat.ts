// About-frame isolation for the Projects chat thread: "Show only this"
// filters to one focus label; leaving isolation restores scroll.
// Framing (About "…") and filter live here — not in backend.

import type { ChatMessage } from "../types.js";

export type IsolateChat = {
  /** Drop isolation (full thread again). */
  clear: () => void;
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

export function createIsolateChat(options: IsolateChatOptions): IsolateChat {
  const { threadEl, resolveStepId, onChange } = options;
  let isolatedFocus: string | null = null;
  let preIsolationScrollTop: number | null = null;

  function messageRow(message: ChatMessage): HTMLDivElement {
    const row = document.createElement("div");
    row.className = `message message-${message.role === "user" ? "you" : "agent"}`;
    const label = document.createElement("span");
    label.className = "who";
    label.textContent = message.role === "user" ? "You" : "Agent";
    const body = document.createElement("span");
    body.className = "text";
    body.textContent = message.text;
    row.append(label, body);
    return row;
  }

  function isolationBanner(): HTMLDivElement {
    const banner = document.createElement("div");
    banner.className = "thread-isolation-banner";
    const label = document.createElement("span");
    label.textContent = `Showing only: About “${isolatedFocus}”`;
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
  ): void {
    threadEl.innerHTML = "";

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
