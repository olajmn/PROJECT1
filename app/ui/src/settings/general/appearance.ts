// General — Appearance: light / dark plane (design base before frosted).

import { getTheme, setTheme, type Theme } from "../../user/theme.js";

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Fill `#appearance` with a Light / Dark control. */
export function mountAppearance(host: HTMLElement): void {
  host.replaceChildren();

  const title = el("h2", "settings-appearance-title", "Appearance");
  const hint = el(
    "p",
    "settings-appearance-hint",
    "Base contrast plane. Frosted layers sit on top of either.",
  );

  const group = el("div", "settings-theme-options");
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", "Theme");

  const current = getTheme();
  for (const theme of ["light", "dark"] as const) {
    const btn = el("button", "settings-theme-option", theme === "light" ? "Light" : "Dark");
    btn.type = "button";
    btn.dataset.theme = theme;
    if (theme === current) btn.setAttribute("aria-pressed", "true");
    else btn.setAttribute("aria-pressed", "false");
    btn.addEventListener("click", () => {
      setTheme(theme);
      syncPressed(group, theme);
    });
    group.appendChild(btn);
  }

  host.append(title, hint, group);
}

function syncPressed(group: HTMLElement, active: Theme): void {
  Array.from(group.querySelectorAll<HTMLButtonElement>(".settings-theme-option")).forEach((btn) => {
    const on = btn.dataset.theme === active;
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
}
