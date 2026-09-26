// The list of projects in the sidebar, under the active id.
// Also the Projects show/hide toggle above it.

// Contents
//  1. Types
//  2. Public API
//      - installProjectList()

import { displayProjectTitle } from "./defaultNames.js";
import {
  projectListIdLabel,
  projectsNewestFirst,
} from "./projectOrder.js";
import { projectsForActiveUser } from "./projectsForId.js";
import { getActiveUserId } from "../../user/activeId.js";
import type { ProjectView } from "../../dataShapes.js";

// 1. Types

const PROJECT_LIST_OPEN_KEY = "projects.listOpen";

export type ProjectList = {
  render: () => void;
};

type ProjectListOpts = {
  listEl: HTMLDivElement;
  emptyEl: HTMLParagraphElement;
  toggleEl: HTMLButtonElement;
  getProjects: () => ProjectView[];
  getSelectedId: () => number | null;
  onSelectProject: (projectId: number) => void;
};

function readListManuallyOpen(): boolean {
  try {
    const stored = localStorage.getItem(PROJECT_LIST_OPEN_KEY);
    return stored === null ? true : stored === "1";
  } catch {
    return true;
  }
}

// 2. Public API

export function installProjectList(opts: ProjectListOpts): ProjectList {
  let listManuallyOpen = readListManuallyOpen();

  const render = (): void => {
    const listVisible = listManuallyOpen;
    opts.toggleEl.classList.toggle("is-active", listVisible);
    opts.toggleEl.setAttribute("aria-expanded", String(listVisible));
    if (!listVisible) {
      opts.listEl.hidden = true;
      opts.listEl.innerHTML = "";
      opts.emptyEl.hidden = true;
      return;
    }
    opts.listEl.hidden = false;
    const projects = opts.getProjects();
    const visible = projectsForActiveUser(projects);
    opts.listEl.innerHTML = "";
    const userId = getActiveUserId();
    if (userId === null) {
      opts.emptyEl.hidden = false;
      opts.emptyEl.textContent =
        "Pick or create an id (click the label above) first.";
    } else {
      opts.emptyEl.hidden = visible.length > 0;
      opts.emptyEl.textContent =
        visible.length > 0 ? "" : "No projects for this id yet.";
    }
    const selectedId = opts.getSelectedId();
    for (const project of projectsNewestFirst(visible)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "project-list-item";
      if (project.project_id === selectedId) {
        button.classList.add("is-selected");
      }
      const title = document.createElement("span");
      title.className = "project-list-title";
      title.textContent = displayProjectTitle(project.name);
      const id = document.createElement("span");
      id.className = "entity-id";
      id.textContent = projectListIdLabel(visible, project);
      button.append(title, id);
      button.addEventListener("click", () => {
        opts.onSelectProject(project.project_id);
      });
      opts.listEl.appendChild(button);
    }
  };

  opts.toggleEl.addEventListener("click", () => {
    listManuallyOpen = !listManuallyOpen;
    try {
      localStorage.setItem(
        PROJECT_LIST_OPEN_KEY,
        listManuallyOpen ? "1" : "0",
      );
    } catch {
      /* private mode / quota — manual toggle is best-effort */
    }
    render();
  });

  return { render };
}
