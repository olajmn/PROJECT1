// Accounts panel: accounts + nested projects, claim orphans.
// Opens in-flow under the brand. Closes only via the Accounts brand
// (toggle) — not outside click or Escape. Create / rename / delete
// live in Settings → Directory.

// Contents
//  1. Types
//  2. Public API
//      - installAccountsPanel()

import { setButtonBusy } from "../../../shell/busyButton.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
  ACCOUNTS_BRAND,
} from "../../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../../dataShapes.js";
import { buildAccountCard } from "./accountCard.js";
import { claimUnassigned, showError } from "./helpers.js";

// 1. Types

const OPEN_KEY = "accounts.panelOpen";
const LEGACY_OPEN_KEY = "projects.idMenuOpen";

export type AccountsPanelOptions = {
  anchor: HTMLElement;
  host: HTMLElement;
  getUsers: () => AccountView[];
  getProjects: () => ProjectView[];
  getSelectedId: () => number | null;
  onUsersChanged: (users: AccountView[]) => void;
  onProjectsUpdated: (updated: ProjectView[]) => void;
  onActiveUserChanged: (userId: number | null) => void;
  onSelectProject: (projectId: number) => void;
};

export type AccountsPanelApi = {
  open: () => void;
  close: () => void;
  toggle: () => void;
  isOpen: () => boolean;
  refresh: () => void;
  /** Call after users/projects are loaded — reopen if left open last time. */
  restoreIfRemembered: () => void;
};

function readRememberedOpen(): boolean {
  try {
    const next = localStorage.getItem(OPEN_KEY);
    if (next !== null) return next !== "0";
    const legacy = localStorage.getItem(LEGACY_OPEN_KEY);
    if (legacy !== null) return legacy !== "0";
  } catch {
    /* ignore */
  }
  return true;
}

// 2. Public API

export function installAccountsPanel(
  opts: AccountsPanelOptions,
): AccountsPanelApi {
  const menu = document.createElement("div");
  menu.className = "sidebar-accounts-panel";
  menu.hidden = true;
  menu.setAttribute("role", "region");
  menu.setAttribute("aria-label", "Accounts");
  opts.host.appendChild(menu);

  const list = document.createElement("div");
  list.className = "sidebar-accounts-list";
  menu.appendChild(list);

  const foot = document.createElement("div");
  foot.className = "sidebar-accounts-foot";
  menu.appendChild(foot);

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
    opts.anchor.textContent = ACCOUNTS_BRAND;
  };

  /** Keep "+" in the Accounts block: under the active card when open,
   * otherwise under the brand — never park it above Settings. */
  const placeCreateButton = (activeCard: HTMLElement | null): void => {
    const btn = document.getElementById("create-open");
    if (!(btn instanceof HTMLButtonElement)) return;
    if (activeCard) {
      activeCard.appendChild(btn);
      btn.classList.add("sidebar-add--under-account");
      return;
    }
    btn.classList.remove("sidebar-add--under-account");
    const afterBrand = opts.anchor.nextSibling;
    if (afterBrand) opts.host.insertBefore(btn, afterBrand);
    else opts.host.appendChild(btn);
  };

  const api: AccountsPanelApi = {
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
      placeCreateButton(null);
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
      if (readRememberedOpen()) api.open();
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
    // Park "+" outside the list first — innerHTML would destroy it if it
    // were still nested under an account card.
    placeCreateButton(null);
    list.innerHTML = "";
    foot.innerHTML = "";

    const users = opts.getUsers().filter((u) => !u.archived);
    const projects = opts.getProjects();
    let activeId = getActiveUserId();
    if (activeId !== null && !users.some((u) => u.id === activeId)) {
      activeId = null;
      setActiveUserId(null);
    }

    if (users.length === 0) {
      const empty = document.createElement("p");
      empty.className = "sidebar-accounts-empty";
      empty.textContent =
        "No accounts yet — create one in Settings → Directory.";
      list.appendChild(empty);
      placeCreateButton(null);
    } else {
      let activeCard: HTMLElement | null = null;
      for (const user of users) {
        const card = buildAccountCard(user, activeId === user.id, projects, {
          getUsers: opts.getUsers,
          getSelectedId: opts.getSelectedId,
          onUsersChanged: opts.onUsersChanged,
          onActiveUserChanged: opts.onActiveUserChanged,
          onSelectProject: opts.onSelectProject,
          afterChange,
        });
        list.appendChild(card);
        if (activeId === user.id) activeCard = card;
      }
      placeCreateButton(activeCard);
    }

    const orphans = projects.filter((p) => p.sim_user_id === null);
    if (orphans.length > 0 && activeId !== null) {
      const claim = document.createElement("button");
      claim.type = "button";
      claim.className = "sidebar-accounts-claim";
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
      note.className = "sidebar-accounts-empty";
      note.textContent = `${orphans.length} project(s) have no account yet.`;
      foot.appendChild(note);
    }
  }
}
