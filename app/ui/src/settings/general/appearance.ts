// General — Appearance: the Light / Dark theme.

import { getTheme, setTheme, type Theme } from "../../user/theme.js";
import { settingsGroup, settingsRow, settingsSection } from "../rows.js";

/** Fill `#appearance` with a Theme row and its Light / Dark control. */
export function mountAppearance(host: HTMLElement): void {
  const control = document.createElement("div");
  control.className = "settings-segmented";
  control.setAttribute("role", "group");
  control.setAttribute("aria-label", "Theme");

  const current = getTheme();
  for (const theme of ["light", "dark"] as const) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = theme === "light" ? "Light" : "Dark";
    btn.dataset.theme = theme;
    btn.setAttribute("aria-pressed", theme === current ? "true" : "false");
    btn.addEventListener("click", () => {
      setTheme(theme);
      syncPressed(control, theme);
    });
    control.appendChild(btn);
  }

  host.replaceChildren(
    settingsSection("Appearance", settingsGroup([settingsRow("Theme", undefined, [control])])),
  );
}

function syncPressed(control: HTMLElement, active: Theme): void {
  control.querySelectorAll<HTMLButtonElement>("button").forEach((btn) => {
    btn.setAttribute("aria-pressed", btn.dataset.theme === active ? "true" : "false");
  });
}
