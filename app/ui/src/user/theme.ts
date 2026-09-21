// UI theme preference (light | dark). Wire: html[data-theme] + localStorage.

const STORAGE_KEY = "ui.theme";

export type Theme = "light" | "dark";

export function getTheme(): Theme {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw === "dark" ? "dark" : "light";
}

export function applyTheme(theme: Theme = getTheme()): void {
  document.documentElement.setAttribute("data-theme", theme);
}

export function setTheme(theme: Theme): void {
  localStorage.setItem(STORAGE_KEY, theme);
  applyTheme(theme);
}

/** Apply stored theme (call early on each page entry). */
export function applyStoredTheme(): void {
  applyTheme(getTheme());
}
