// Sidebar id#N panel: rich overview (ids + their projects), create,
// claim orphans. Opens in-flow under the brand so Create / project list
// shift down; optional vertical resize caps the scroll area.

// Contents
//  1. Types
//  2. Public API
//      - installIdMenu()
//  3. Helpers
//      - claimUnassigned()
//      - showError()

import { archiveUser, createUser, setProjectUser } from "../api.js";
import { setButtonBusy } from "../shell/busy.js";
import {
  projectListIdLabel,
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "./projectListOrder.js";
import { getActiveUserId, setActiveUserId, userLabel, ID_BRAND } from "../user/activeUser.js";
import type { ProjectView, UserView } from "../types.js";

// 1. Types

const HEIGHT_KEY = "projects.idMenuListHeightPx";
const MIN_LIST_HEIGHT = 120;
const MAX_LIST_HEIGHT = 560;

export type IdMenuOptions = {
  anchor: HTMLElement;
  host: HTMLElement;
  getUsers: () => UserView[];
  getProjects: () => ProjectView[];
  onUsersChanged: (users: UserView[]) => void;
  onProjectsUpdated: (updated: ProjectView[]) => void;
  onActiveUserChanged: (userId: number | null) => void;
  onSelectProject: (projectId: number) => void;
};

export type IdMenuApi = {
  open: () => void;
  close: () => void;
  toggle: () => void;
  isOpen: () => boolean;
  refresh: () => void;
};

// 2. Public API

export function installIdMenu(opts: IdMenuOptions): IdMenuApi {
  const menu = document.createElement("div");
  menu.className = "sidebar-id-menu";
  menu.hidden = true;
  menu.setAttribute("role", "region");
  menu.setAttribute("aria-label", "Ids");
  opts.host.appendChild(menu);

  const list = document.createElement("div");
  list.className = "sidebar-id-menu-list";
  menu.appendChild(list);

  const foot = document.createElement("div");
  foot.className = "sidebar-id-menu-foot";
  menu.appendChild(foot);

  const resize = document.createElement("div");
  resize.className = "sidebar-id-menu-resize";
  resize.title = "Drag to set max height";
  resize.setAttribute("aria-hidden", "true");
  menu.appendChild(resize);

  applyStoredHeight();
  installResize(resize);

  let open = false;

  const api: IdMenuApi = {
    open: () => {
      if (open) return;
      open = true;
      rebuild();
      menu.hidden = false;
      opts.anchor.setAttribute("aria-expanded", "true");
      opts.anchor.classList.add("is-active");
    },
    close: () => {
      if (!open) return;
      open = false;
      menu.hidden = true;
      opts.anchor.setAttribute("aria-expanded", "false");
      opts.anchor.classList.remove("is-active");
    },
    toggle: () => {
      if (open) api.close();
      else api.open();
    },
    isOpen: () => open,
    refresh: () => {
      if (open) rebuild();
    },
  };

  opts.anchor.setAttribute("aria-haspopup", "true");
  opts.anchor.setAttribute("aria-expanded", "false");
  opts.anchor.addEventListener("click", (event) => {
    event.stopPropagation();
    api.toggle();
  });

  // Column-width drag uses `#sidebar-resize` outside the menu. Treat that
  // gesture as not an outside click, including when pointerup lands elsewhere.
  let ignoreOutsideClick = false;
  document.addEventListener(
    "pointerdown",
    (event) => {
      const target = event.target;
      if (target instanceof Element && target.closest(".sidebar-resize")) {
        ignoreOutsideClick = true;
      }
    },
    true,
  );
  document.addEventListener(
    "pointerup",
    () => {
      if (!ignoreOutsideClick) return;
      // Survive the click that follows this pointerup in the same gesture.
      setTimeout(() => {
        ignoreOutsideClick = false;
      }, 0);
    },
    true,
  );

  document.addEventListener("click", (event) => {
    if (!open) return;
    if (ignoreOutsideClick) return;
    const target = event.target as Node | null;
    if (target && (menu.contains(target) || opts.anchor.contains(target))) {
      return;
    }
    if (target instanceof Element && target.closest(".sidebar-resize")) {
      return;
    }
    api.close();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && open) api.close();
  });

  return api;

  function rebuild(): void {
    list.innerHTML = "";
    foot.innerHTML = "";

    const allUsers = opts.getUsers();
    const users = allUsers.filter((u) => !u.archived);
    const projects = opts.getProjects();
    let activeId = getActiveUserId();
    if (activeId !== null && !users.some((u) => u.id === activeId)) {
      activeId = null;
      setActiveUserId(null);
    }

    if (users.length === 0) {
      const empty = document.createElement("p");
      empty.className = "sidebar-id-menu-empty";
      empty.textContent = "No ids yet — create one below.";
      list.appendChild(empty);
    } else {
      for (const user of users) {
        list.appendChild(userCard(user, activeId === user.id, projects));
      }
    }

    const orphans = projects.filter((p) => p.sim_user_id === null);
    if (orphans.length > 0 && activeId !== null) {
      const claim = document.createElement("button");
      claim.type = "button";
      claim.className = "sidebar-id-menu-claim";
      claim.textContent = `Assign ${orphans.length} unowned → ${userLabel(
        users.find((u) => u.id === activeId) ?? { id: activeId },
      )}`;
      claim.addEventListener("click", async (event) => {
        event.stopPropagation();
        setButtonBusy(claim, true);
        try {
          const claimed = await claimUnassigned(activeId, projects);
          if (claimed.length > 0) opts.onProjectsUpdated(claimed);
          opts.onActiveUserChanged(activeId);
        } catch (err) {
          setButtonBusy(claim, false);
          showError(foot, err);
        }
      });
      foot.appendChild(claim);
    } else if (orphans.length > 0) {
      const note = document.createElement("p");
      note.className = "sidebar-id-menu-empty";
      note.textContent = `${orphans.length} project(s) have no id yet.`;
      foot.appendChild(note);
    }

    foot.appendChild(createForm(allUsers, projects));
  }

  function userCard(
    user: UserView,
    isActive: boolean,
    projects: ProjectView[],
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

    const actions = document.createElement("div");
    actions.className = "sidebar-id-card-actions";

    if (isActive) {
      const mark = document.createElement("span");
      mark.className = "sidebar-id-menu-hint";
      mark.textContent = "active";
      actions.appendChild(mark);
    } else {
      const use = document.createElement("button");
      use.type = "button";
      use.className = "sidebar-id-card-use";
      use.textContent = "Use";
      use.addEventListener("click", (event) => {
        event.stopPropagation();
        setActiveUserId(user.id);
        opts.onActiveUserChanged(user.id);
        rebuild();
        renderBrandOnly();
      });
      actions.appendChild(use);
    }

    const del = document.createElement("button");
    del.type = "button";
    del.className = "sidebar-id-card-delete";
    del.textContent = "Delete";
    del.title = "Remove this id (projects stay, unlinked)";
    del.addEventListener("click", async (event) => {
      event.stopPropagation();
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
        const next = opts.getUsers().map((u) =>
          u.id === archived.id ? archived : u,
        );
        if (getActiveUserId() === user.id) {
          setActiveUserId(null);
          opts.onActiveUserChanged(null);
        }
        opts.onUsersChanged(next);
        rebuild();
        renderBrandOnly();
      } catch (err) {
        setButtonBusy(del, false);
        showError(card, err);
      }
    });
    actions.appendChild(del);
    top.appendChild(actions);
    card.appendChild(top);

    const linked = projectsChronologicalForUser(projects, user.id);
    const group = document.createElement("div");
    group.className = "sidebar-id-card-projects";
    if (linked.length === 0) {
      const empty = document.createElement("p");
      empty.className = "sidebar-id-menu-empty";
      empty.textContent = "No projects yet";
      group.appendChild(empty);
    } else {
      for (const project of projectsNewestFirst(linked)) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "sidebar-id-card-project";
        const goal = document.createElement("span");
        goal.className = "sidebar-id-card-project-goal";
        goal.textContent = project.goal;
        const id = document.createElement("span");
        id.className = "sidebar-id-menu-hint";
        id.textContent = projectListIdLabel(linked, project);
        row.append(goal, id);
        row.addEventListener("click", (event) => {
          event.stopPropagation();
          if (!isActive) {
            setActiveUserId(user.id);
            opts.onActiveUserChanged(user.id);
          }
          opts.onSelectProject(project.project_id);
          api.close();
        });
        group.appendChild(row);
      }
    }
    card.appendChild(group);
    return card;
  }

  function createForm(
    allUsers: UserView[],
    projects: ProjectView[],
  ): HTMLFormElement {
    const form = document.createElement("form");
    form.className = "sidebar-id-menu-create";
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Optional label…";
    const button = document.createElement("button");
    button.type = "submit";
    button.textContent = "Create id";
    form.append(input, button);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      setButtonBusy(button, true);
      input.disabled = true;
      try {
        const label = input.value.trim() || "user";
        const created = await createUser(label);
        const claimed = await claimUnassigned(created.id, projects);
        opts.onUsersChanged([...allUsers, created]);
        if (claimed.length > 0) opts.onProjectsUpdated(claimed);
        setActiveUserId(created.id);
        opts.onActiveUserChanged(created.id);
        rebuild();
        renderBrandOnly();
      } catch (err) {
        setButtonBusy(button, false);
        input.disabled = false;
        showError(form, err);
      }
    });
    return form;
  }

  function renderBrandOnly(): void {
    opts.anchor.textContent = ID_BRAND;
  }

  /** Optional cap only — default is natural height (shows everything). */
  function applyStoredHeight(): void {
    const h = Number(localStorage.getItem(HEIGHT_KEY));
    if (!Number.isFinite(h) || h < MIN_LIST_HEIGHT) return;
    const capped = Math.min(MAX_LIST_HEIGHT, h);
    list.style.maxHeight = `${capped}px`;
  }

  function installResize(handle: HTMLElement): void {
    let dragging = false;
    let startY = 0;
    let startH = 0;

    handle.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      event.stopPropagation();
      dragging = true;
      handle.setPointerCapture(event.pointerId);
      startY = event.clientY;
      startH = list.getBoundingClientRect().height;
      document.body.classList.add("is-resizing-id-menu");
    });

    handle.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const nextH = Math.min(
        MAX_LIST_HEIGHT,
        Math.max(MIN_LIST_HEIGHT, Math.round(startH + (event.clientY - startY))),
      );
      list.style.maxHeight = `${nextH}px`;
    });

    const end = (event: PointerEvent) => {
      if (!dragging) return;
      dragging = false;
      handle.releasePointerCapture(event.pointerId);
      document.body.classList.remove("is-resizing-id-menu");
      const h = Math.round(list.getBoundingClientRect().height);
      localStorage.setItem(HEIGHT_KEY, String(h));
    };
    handle.addEventListener("pointerup", end);
    handle.addEventListener("pointercancel", end);
  }
}

// 3. Helpers

async function claimUnassigned(
  userId: number,
  projects: ProjectView[],
): Promise<ProjectView[]> {
  const orphans = projects.filter((p) => p.sim_user_id === null);
  const claimed: ProjectView[] = [];
  for (const orphan of orphans) {
    claimed.push(await setProjectUser(orphan.project_id, userId));
  }
  return claimed;
}

function showError(host: HTMLElement, err: unknown): void {
  const error = document.createElement("p");
  error.className = "error";
  error.textContent = `(error: ${(err as Error).message})`;
  host.appendChild(error);
}
