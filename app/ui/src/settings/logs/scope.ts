// Logs scope control — All activity vs one project's full timeline.
// Updates ?project= in the URL so a project tape can be bookmarked.

import { fetchProjects } from "../../api.js";
import { el } from "../register/dom.js";

export type LogScope =
  | { kind: "all" }
  | { kind: "project"; projectId: number };

function scopeFromUrl(): LogScope {
  const raw = new URLSearchParams(location.search).get("project");
  if (!raw) return { kind: "all" };
  const projectId = Number(raw);
  if (!Number.isInteger(projectId) || projectId < 1) return { kind: "all" };
  return { kind: "project", projectId };
}

function writeUrl(scope: LogScope): void {
  const url = new URL(location.href);
  if (scope.kind === "all") {
    url.searchParams.delete("project");
  } else {
    url.searchParams.set("project", String(scope.projectId));
  }
  history.replaceState(null, "", url);
}

/** Mount the project picker; call `onChange` when the scope changes. */
export async function mountLogScope(
  host: HTMLElement,
  onChange: (scope: LogScope) => void,
): Promise<LogScope> {
  host.replaceChildren();

  const label = el("label", "settings-logs-scope-label", "Show");
  label.htmlFor = "logs-scope";
  const select = el("select", "settings-logs-scope");
  select.id = "logs-scope";
  select.setAttribute("aria-label", "Log scope");

  const allOpt = document.createElement("option");
  allOpt.value = "";
  allOpt.textContent = "All activity";
  select.appendChild(allOpt);

  let initial = scopeFromUrl();

  try {
    const projects = await fetchProjects();
    const open = projects
      .filter((p) => !p.cancelled)
      .sort((a, b) => a.name.localeCompare(b.name) || a.project_id - b.project_id);

    for (const p of open) {
      const opt = document.createElement("option");
      opt.value = String(p.project_id);
      opt.textContent = `${p.name} (#${p.project_id})`;
      select.appendChild(opt);
    }

    if (initial.kind === "project") {
      const wanted = initial.projectId;
      if (!open.some((p) => p.project_id === wanted)) {
        initial = { kind: "all" };
        writeUrl(initial);
      }
    }
  } catch {
    // Picker still works for All activity if the project list fails.
    if (initial.kind === "project") {
      initial = { kind: "all" };
      writeUrl(initial);
    }
  }

  select.value =
    initial.kind === "project" ? String(initial.projectId) : "";

  select.addEventListener("change", () => {
    const scope: LogScope = select.value
      ? { kind: "project", projectId: Number(select.value) }
      : { kind: "all" };
    writeUrl(scope);
    onChange(scope);
  });

  const hint = el(
    "p",
    "settings-logs-scope-hint",
    "All activity is the mixed feed (newest first). A project shows its full ungrouped timeline, oldest first.",
  );

  host.append(label, select, hint);
  return initial;
}
