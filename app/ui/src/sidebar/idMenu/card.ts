// One id column: label, ⋯ (Use / Delete), projects stacked under it.

import { archiveUser } from "../../api.js";
import { displayProjectTitle } from "../../create/autoname.js";
import { setButtonBusy } from "../../shell/busy.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
} from "../../user/activeUser.js";
import type { ProjectView, UserView } from "../../types.js";
import {
  projectListIdLabel,
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "../projectListOrder.js";
import { closeIdCardMenus, showError } from "./helpers.js";

export type IdCardCallbacks = {
  getUsers: () => UserView[];
  onUsersChanged: (users: UserView[]) => void;
  onActiveUserChanged: (userId: number | null) => void;
  onSelectProject: (projectId: number) => void;
  /** Rebuild menu + brand after Use / Delete. */
  afterChange: () => void;
};

export function buildIdCard(
  user: UserView,
  isActive: boolean,
  projects: ProjectView[],
  cb: IdCardCallbacks,
): HTMLElement {
  const card = document.createElement("article");
  card.className = "sidebar-id-card";
  if (isActive) card.classList.add("is-active");

  const top = document.createElement("div");
  top.className = "sidebar-id-card-top";

  const titleWrap = document.createElement("div");
  titleWrap.className = "sidebar-id-card-title";
  const name = document.createElement("span");
  name.className = "sidebar-id-menu-hint";
  name.textContent = userLabel(user);
  titleWrap.appendChild(name);
  top.appendChild(titleWrap);

  top.appendChild(buildOptionsMenu(user, isActive, card, cb));
  card.appendChild(top);
  card.appendChild(buildProjectGroup(user, isActive, projects, cb));
  return card;
}

function buildOptionsMenu(
  user: UserView,
  isActive: boolean,
  card: HTMLElement,
  cb: IdCardCallbacks,
): HTMLElement {
  const menuWrap = document.createElement("div");
  menuWrap.className = "sidebar-id-card-menu-wrap";

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "sidebar-id-card-menu-toggle";
  toggle.textContent = "⋯";
  toggle.title = "Id options";
  toggle.setAttribute("aria-haspopup", "true");
  toggle.setAttribute("aria-expanded", "false");

  const menu = document.createElement("div");
  menu.className = "sidebar-id-card-menu";
  menu.hidden = true;
  menu.setAttribute("role", "menu");

  if (!isActive) {
    const use = document.createElement("button");
    use.type = "button";
    use.className = "sidebar-id-card-menu-item";
    use.setAttribute("role", "menuitem");
    use.textContent = "Use";
    use.addEventListener("click", (event) => {
      event.stopPropagation();
      closeIdCardMenus();
      setActiveUserId(user.id);
      cb.onActiveUserChanged(user.id);
      cb.afterChange();
    });
    menu.appendChild(use);
  }

  const del = document.createElement("button");
  del.type = "button";
  del.className = "sidebar-id-card-menu-item";
  del.setAttribute("role", "menuitem");
  del.textContent = "Delete";
  del.title = "Remove this id (projects stay, unlinked)";
  del.addEventListener("click", async (event) => {
    event.stopPropagation();
    closeIdCardMenus();
    const label = userLabel(user);
    if (
      !window.confirm(
        `Delete ${label}?\n\nProjects stay; they just lose this id link.`,
      )
    ) {
      return;
    }
    setButtonBusy(del, true);
    try {
      const archived = await archiveUser(user.id);
      const next = cb.getUsers().map((u) =>
        u.id === archived.id ? archived : u,
      );
      if (getActiveUserId() === user.id) {
        setActiveUserId(null);
        cb.onActiveUserChanged(null);
      }
      cb.onUsersChanged(next);
      cb.afterChange();
    } catch (err) {
      setButtonBusy(del, false);
      showError(card, err);
    }
  });
  menu.appendChild(del);

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const opening = menu.hidden;
    closeIdCardMenus();
    if (opening) {
      menu.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
    }
  });

  menuWrap.append(toggle, menu);
  return menuWrap;
}

function buildProjectGroup(
  user: UserView,
  isActive: boolean,
  projects: ProjectView[],
  cb: IdCardCallbacks,
): HTMLElement {
  const linked = projectsChronologicalForUser(projects, user.id);
  const group = document.createElement("div");
  group.className = "sidebar-id-card-projects";
  if (linked.length === 0) {
    const empty = document.createElement("p");
    empty.className = "sidebar-id-menu-empty";
    empty.textContent = "No projects yet";
    group.appendChild(empty);
    return group;
  }
  for (const project of projectsNewestFirst(linked)) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "sidebar-id-card-project";
    const goal = document.createElement("span");
    goal.className = "sidebar-id-card-project-goal";
    goal.textContent = displayProjectTitle(project.goal);
    const id = document.createElement("span");
    id.className = "sidebar-id-menu-hint";
    id.textContent = projectListIdLabel(linked, project);
    row.append(goal, id);
    row.addEventListener("click", (event) => {
      event.stopPropagation();
      if (!isActive) {
        setActiveUserId(user.id);
        cb.onActiveUserChanged(user.id);
      }
      cb.onSelectProject(project.project_id);
    });
    group.appendChild(row);
  }
  return group;
}
