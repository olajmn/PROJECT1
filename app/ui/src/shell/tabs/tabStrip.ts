// Closable topbar tab strip (shell chrome).

// Contents
//  1. Types
//  2. Build
//      - makeTab()
//      - renderTabStrip()

// 1. Types

export type TabStripItem = {
  id: string;
  label: string;
  selected: boolean;
  onSelect: () => void;
  onClose: () => void;
};

// 2. Build

function makeTab(item: TabStripItem): HTMLDivElement {
  const tab = document.createElement("div");
  tab.className = "project-tab";
  tab.setAttribute("role", "tab");
  tab.setAttribute("aria-selected", item.selected ? "true" : "false");
  if (item.selected) tab.classList.add("is-active");
  tab.tabIndex = 0;
  tab.dataset.tabId = item.id;

  const labelEl = document.createElement("span");
  labelEl.className = "project-tab-label";
  labelEl.textContent = item.label;
  tab.appendChild(labelEl);

  const close = document.createElement("button");
  close.type = "button";
  close.className = "project-tab-close";
  close.setAttribute("aria-label", `Close ${item.label}`);
  close.textContent = "×";
  close.addEventListener("click", (event) => {
    event.stopPropagation();
    item.onClose();
  });
  tab.appendChild(close);

  const activate = () => {
    if (item.selected) return;
    item.onSelect();
  };
  tab.addEventListener("click", activate);
  tab.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activate();
    }
  });
  return tab;
}

/** Tablist of closable chips for the project topbar. */
export function renderTabStrip(items: TabStripItem[]): HTMLDivElement {
  const tabs = document.createElement("div");
  tabs.className = "project-tabs";
  tabs.setAttribute("role", "tablist");
  for (const item of items) {
    tabs.appendChild(makeTab(item));
  }
  return tabs;
}
