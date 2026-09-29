// Archive — Settings → Archive: soft-archived accounts and closed
// projects; restore or permanently delete. One row each (../rows.ts).

// Contents
//  1. Rows
//      - accountRow() / projectRow()
//  2. mountArchive()

import {
  deleteAccount,
  deleteProject,
  fetchAccounts,
  fetchArchivedProjects,
  restoreAccount,
  restoreProject,
} from "../../api.js";
import { askToConfirm } from "../../panes/canvas/confirmPopover.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import { accountWireLabel, userLabel } from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import {
  settingsAction,
  settingsGroup,
  settingsListRow,
  settingsSection,
  shortDate,
} from "../rows.js";

// 1. Rows

/** Run `work` with the button busy; on failure the button comes back. */
async function busy(button: HTMLButtonElement, work: () => Promise<void>): Promise<void> {
  setButtonBusy(button, true);
  try {
    await work();
  } catch {
    setButtonBusy(button, false);
  }
}

/** Restore (when allowed) and Delete; delete asks first, it cannot be
 *  undone. */
function actions(
  what: string,
  onRestore: (() => Promise<void>) | null,
  onDelete: () => Promise<void>,
): HTMLButtonElement[] {
  const out: HTMLButtonElement[] = [];
  if (onRestore) {
    out.push(settingsAction("Restore", (btn) => void busy(btn, onRestore)));
  }
  out.push(
    settingsAction(
      "Delete",
      async (btn) => {
        const ok = await askToConfirm(
          btn.getBoundingClientRect(),
          `Delete ${what} for good? This cannot be undone.`,
          "Delete",
        );
        if (ok) await busy(btn, onDelete);
      },
      true,
    ),
  );
  return out;
}

function accountRow(account: AccountView, repaint: () => Promise<void>): HTMLElement {
  // The id leads, so every account reads the same; its own name follows
  // only when it has one (an unnamed account's label is just its id).
  const name = userLabel(account);
  const id = accountWireLabel(account.id);
  const details = [name === id ? "" : name, shortDate(account.created_at)]
    .filter(Boolean)
    .join(" · ");
  return settingsListRow(
    id,
    details,
    actions(
      `“${userLabel(account)}”`,
      async () => {
        await restoreAccount(account.id);
        await repaint();
      },
      async () => {
        await deleteAccount(account.id);
        await repaint();
      },
    ),
  );
}

function projectStatus(project: ProjectView): string {
  if (project.cancelled) return "Archived";
  if (project.completed) return "Completed";
  return "Closed";
}

function projectRow(project: ProjectView, repaint: () => Promise<void>): HTMLElement {
  const local = project.account_n != null ? `#${project.account_n}` : `#${project.project_id}`;
  const details = [local, projectStatus(project), shortDate(project.created_at)]
    .filter(Boolean)
    .join(" · ");
  const canRestore = project.cancelled && !project.completed;
  return settingsListRow(
    project.name,
    details,
    actions(
      `“${project.name}”`,
      canRestore
        ? async () => {
            await restoreProject(project.project_id);
            await repaint();
          }
        : null,
      async () => {
        await deleteProject(project.project_id);
        await repaint();
      },
    ),
  );
}

// 2. mountArchive()

type ArchiveFilter = "all" | "accounts" | "projects";

export async function mountArchive(host: HTMLElement): Promise<void> {
  const hint = document.createElement("p");
  hint.className = "settings-hint";
  hint.textContent = "Archived accounts and closed projects. Restore brings one back; delete removes it for good.";

  const filterBar = document.createElement("div");
  filterBar.className = "settings-segmented";
  filterBar.setAttribute("role", "group");
  filterBar.setAttribute("aria-label", "Show");

  const lists = document.createElement("div");
  lists.className = "settings-lists";
  const empty = document.createElement("p");
  empty.className = "settings-hint";
  empty.hidden = true;
  const error = document.createElement("p");
  error.className = "error";
  error.hidden = true;
  host.replaceChildren(hint, filterBar, lists, empty, error);

  // Survives repaints, so restore / delete keeps the current view.
  let filter: ArchiveFilter = "all";
  let archivedAccounts: AccountView[] = [];
  let projects: ProjectView[] = [];

  const filterButtons = new Map<ArchiveFilter, HTMLButtonElement>();
  for (const key of ["all", "accounts", "projects"] as ArchiveFilter[]) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.addEventListener("click", () => {
      filter = key;
      render();
    });
    filterButtons.set(key, btn);
    filterBar.appendChild(btn);
  }

  const paint = async (): Promise<void> => {
    error.hidden = true;
    try {
      const [accounts, archivedProjects] = await Promise.all([
        fetchAccounts(),
        fetchArchivedProjects(),
      ]);
      archivedAccounts = accounts.filter((a) => a.archived);
      projects = archivedProjects;
      render();
    } catch (err) {
      lists.replaceChildren();
      empty.hidden = true;
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    }
  };

  const render = (): void => {
    const counts: Record<ArchiveFilter, number> = {
      all: archivedAccounts.length + projects.length,
      accounts: archivedAccounts.length,
      projects: projects.length,
    };
    const labels: Record<ArchiveFilter, string> = {
      all: "All",
      accounts: "Accounts",
      projects: "Projects",
    };
    for (const [key, btn] of filterButtons) {
      btn.textContent = `${labels[key]} ${counts[key]}`;
      btn.setAttribute("aria-pressed", String(key === filter));
    }

    lists.replaceChildren();
    if (filter !== "projects" && archivedAccounts.length > 0) {
      lists.appendChild(
        settingsSection(
          "Accounts",
          settingsGroup(archivedAccounts.map((a) => accountRow(a, paint))),
        ),
      );
    }
    if (filter !== "accounts" && projects.length > 0) {
      lists.appendChild(
        settingsSection(
          "Projects",
          settingsGroup(projects.map((p) => projectRow(p, paint))),
        ),
      );
    }

    empty.hidden = counts[filter] > 0;
    empty.textContent =
      filter === "accounts"
        ? "No archived accounts."
        : filter === "projects"
          ? "No closed projects."
          : "Nothing in the archive.";
  };

  await paint();
}
