// One account column: label (click = expand/collapse projects),
// projects stacked under it when expanded. Account create / rename /
// delete live in Settings → Directory.

import { displayProjectTitle } from "../defaultNames.js";
import {
  setActiveUserId,
  userLabel,
  accountWireLabel,
} from "../../../user/activeAccount.js";
import type { ProjectView, UserView } from "../../../dataShapes.js";
import {
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "../projectOrder.js";

const EXPANDED_KEY = "accounts.cardExpanded";

export type AccountCardCallbacks = {
  getUsers: () => UserView[];
  getSelectedId: () => number | null;
  onUsersChanged: (users: UserView[]) => void;
  onActiveUserChanged: (userId: number | null) => void;
  onSelectProject: (projectId: number) => void;
  /** Rebuild panel + brand after active-account change. */
  afterChange: () => void;
};

function readExpandedMap(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(EXPANDED_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, boolean>;
    }
  } catch {
    /* private mode / bad JSON */
  }
  return {};
}

function writeExpanded(userId: number, open: boolean): void {
  try {
    const map = readExpandedMap();
    map[String(userId)] = open;
    localStorage.setItem(EXPANDED_KEY, JSON.stringify(map));
  } catch {
    /* best-effort */
  }
}

/** Remembered expand state; active account defaults open. */
export function isAccountCardExpanded(
  userId: number,
  isActive: boolean,
): boolean {
  const map = readExpandedMap();
  const key = String(userId);
  if (Object.prototype.hasOwnProperty.call(map, key)) return map[key] === true;
  return isActive;
}

export function buildAccountCard(
  user: UserView,
  isActive: boolean,
  projects: ProjectView[],
  cb: AccountCardCallbacks,
): HTMLElement {
  const card = document.createElement("article");
  card.className = "sidebar-account-card";
  if (isActive) card.classList.add("is-active");

  let expanded = isAccountCardExpanded(user.id, isActive);

  const top = document.createElement("div");
  top.className = "sidebar-account-card-top";

  const titleWrap = document.createElement("div");
  titleWrap.className = "sidebar-account-card-title";
  const name = document.createElement("button");
  name.type = "button";
  name.className = "sidebar-account-card-name";
  name.textContent = userLabel(user);
  name.title = expanded ? "Hide projects" : "Show projects";
  name.setAttribute("aria-expanded", String(expanded));
  const wire = document.createElement("span");
  wire.className = "sidebar-account-card-wire";
  wire.textContent = accountWireLabel(user.id);
  // Avoid "account#15" twice when there is no custom name.
  if (wire.textContent === name.textContent) wire.hidden = true;
  titleWrap.append(name, wire);
  top.appendChild(titleWrap);
  card.appendChild(top);

  const group = buildProjectGroup(user, projects, cb);
  group.hidden = !expanded;
  card.appendChild(group);

  name.addEventListener("click", (event) => {
    event.stopPropagation();
    expanded = !expanded;
    writeExpanded(user.id, expanded);
    group.hidden = !expanded;
    name.setAttribute("aria-expanded", String(expanded));
    name.title = expanded ? "Hide projects" : "Show projects";
    if (expanded && !isActive) {
      setActiveUserId(user.id);
      cb.onActiveUserChanged(user.id);
      cb.afterChange();
    }
  });

  return card;
}

function buildProjectGroup(
  user: UserView,
  projects: ProjectView[],
  cb: AccountCardCallbacks,
): HTMLElement {
  const linked = projectsChronologicalForUser(projects, user.id);
  const group = document.createElement("div");
  group.className = "sidebar-account-card-projects";
  if (linked.length === 0) {
    const empty = document.createElement("p");
    empty.className = "sidebar-accounts-empty";
    empty.textContent = "No projects yet";
    group.appendChild(empty);
    return group;
  }
  const selectedId = cb.getSelectedId();
  for (const project of projectsNewestFirst(linked)) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "sidebar-account-card-project";
    if (project.project_id === selectedId) {
      row.classList.add("is-selected");
    }
    const goal = document.createElement("span");
    goal.className = "sidebar-account-card-project-goal";
    goal.textContent = displayProjectTitle(project.name);
    row.append(goal);
    row.addEventListener("click", (event) => {
      event.stopPropagation();
      // onSelectProject sets the active account from the project — don't
      // call onActiveUserChanged first (that runs ensureSelection + render
      // while Create may still be open, and can flash or stick on create).
      cb.onSelectProject(project.project_id);
    });
    group.appendChild(row);
  }
  return group;
}
