// Manager id#N panel: overview columns (ids + their projects), create id,
// claim orphans. Opens in-flow under the brand; optional vertical resize
// caps the scroll area. Closes only via the Manager brand (toggle) — not
// outside click or Escape.

// Contents
//  1. Types
//  2. Public API
//      - installIdMenu()

import { setButtonBusy } from "../../shell/busy.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
  ID_BRAND,
} from "../../user/activeUser.js";
import type { ProjectView, UserView } from "../../types.js";
import { buildIdCard } from "./card.js";
import { buildCreateIdForm } from "./createId.js";
import {
  claimUnassigned,
  ensureIdCardMenuCloser,
  showError,
} from "./helpers.js";
import { applyStoredHeight, installResize } from "./resize.js";

// 1. Types

const OPEN_KEY = "projects.idMenuOpen";

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
  /** Call after users/projects are loaded — reopen if left open last time. */
  restoreIfRemembered: () => void;
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

  applyStoredHeight(list);
  installResize(list, resize);
  ensureIdCardMenuCloser();

  let open = false;

  const rememberOpen = (next: boolean): void => {
    try {
      localStorage.setItem(OPEN_KEY, next ? "1" : "0");
    } catch {
      /* private mode / quota — open state is best-effort */
    }
  };

  const afterChange = (): void => {
    rebuild();
    opts.anchor.textContent = ID_BRAND;
  };

  const api: IdMenuApi = {
    open: () => {
      if (open) return;
      open = true;
      rebuild();
      menu.hidden = false;
      opts.anchor.setAttribute("aria-expanded", "true");
      opts.anchor.classList.add("is-active");
      rememberOpen(true);
    },
    close: () => {
      if (!open) return;
      open = false;
      menu.hidden = true;
      opts.anchor.setAttribute("aria-expanded", "false");
      opts.anchor.classList.remove("is-active");
      rememberOpen(false);
    },
    toggle: () => {
      if (open) api.close();
      else api.open();
    },
    isOpen: () => open,
    refresh: () => {
      if (open) rebuild();
    },
    restoreIfRemembered: () => {
      try {
        if (localStorage.getItem(OPEN_KEY) === "1") api.open();
      } catch {
        /* ignore */
      }
    },
  };

  opts.anchor.setAttribute("aria-haspopup", "true");
  opts.anchor.setAttribute("aria-expanded", "false");
  opts.anchor.addEventListener("click", (event) => {
    event.stopPropagation();
    api.toggle();
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
        list.appendChild(
          buildIdCard(user, activeId === user.id, projects, {
            getUsers: opts.getUsers,
            onUsersChanged: opts.onUsersChanged,
            onActiveUserChanged: opts.onActiveUserChanged,
            onSelectProject: opts.onSelectProject,
            afterChange,
          }),
        );
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

    foot.appendChild(
      buildCreateIdForm(allUsers, projects, {
        onUsersChanged: opts.onUsersChanged,
        onProjectsUpdated: opts.onProjectsUpdated,
        onActiveUserChanged: opts.onActiveUserChanged,
        afterChange,
      }),
    );
  }
}
