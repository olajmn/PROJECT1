// Archive — Settings → Archive: soft-archived accounts and closed
// projects; restore or permanently delete.

// Contents
//  1. Helpers
//  2. mountArchive()

import {
  deleteAccount,
  deleteProject,
  fetchAccounts,
  fetchArchivedProjects,
  restoreAccount,
  restoreProject,
} from "../../api.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import {
  accountWireLabel,
  userLabel,
} from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import {
  arrangeBlock,
  projectBlock,
  startAgeClock,
  type ProjectValues,
} from "../register/index.js";
import type { Block } from "../register/types.js";

// 1. Helpers

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function projectValues(project: ProjectView): ProjectValues {
  return {
    id: project.project_id,
    name: project.name,
    created: project.created_at,
    accountN: project.account_n ?? null,
  };
}

function accountBlock(account: AccountView): Block {
  const block: Block = [
    { t: "title", kind: "Account", name: "" },
    { t: "fact", label: "Name", value: userLabel(account) },
    { t: "fact", label: "Id", value: accountWireLabel(account.id) },
    { t: "fact", label: "Created", created: account.created_at },
  ];
  if (account.archived_at) {
    block.push({ t: "fact", label: "Archived", created: account.archived_at });
  }
  return block;
}

function projectStatus(project: ProjectView): string {
  if (project.cancelled) return "Archived";
  if (project.completed) return "Completed";
  return "Closed";
}

function closedProjectBlock(project: ProjectView): Block {
  const block = projectBlock(projectValues(project));
  block.splice(2, 0, {
    t: "fact",
    label: "Status",
    value: projectStatus(project),
  });
  return block;
}

function actionRow(
  onRestore: (() => Promise<void>) | null,
  onDelete: () => Promise<void>,
  deleteLabel: string,
): HTMLElement {
  const actions = el("div", "directory-account-actions");
  if (onRestore) {
    const restoreBtn = el(
      "button",
      "directory-rename",
      "Restore",
    ) as HTMLButtonElement;
    restoreBtn.type = "button";
    restoreBtn.addEventListener("click", async () => {
      setButtonBusy(restoreBtn, true);
      try {
        await onRestore();
      } catch {
        setButtonBusy(restoreBtn, false);
      }
    });
    actions.appendChild(restoreBtn);
  }

  const deleteBtn = el(
    "button",
    "directory-delete",
    "Delete permanently",
  ) as HTMLButtonElement;
  deleteBtn.type = "button";
  deleteBtn.title = deleteLabel;

  const confirm = el("div", "directory-delete-confirm");
  confirm.hidden = true;
  const hint = el(
    "p",
    "directory-hint",
    "This cannot be undone.",
  );
  const yes = el("button", "directory-delete", "Delete") as HTMLButtonElement;
  yes.type = "button";
  const no = el("button", "directory-rename", "Cancel") as HTMLButtonElement;
  no.type = "button";
  confirm.append(hint, yes, no);

  deleteBtn.addEventListener("click", () => {
    deleteBtn.hidden = true;
    confirm.hidden = false;
  });
  no.addEventListener("click", () => {
    confirm.hidden = true;
    deleteBtn.hidden = false;
  });
  yes.addEventListener("click", async () => {
    setButtonBusy(yes, true);
    try {
      await onDelete();
    } catch {
      setButtonBusy(yes, false);
    }
  });

  actions.append(deleteBtn, confirm);
  return actions;
}

// 2. mountArchive()

type ArchiveFilter = "all" | "accounts" | "projects";

export async function mountArchive(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const hint = el(
    "p",
    "directory-hint",
    "Archived accounts and closed projects. Restore brings them back; delete removes them for good.",
  );
  const filterBar = el("div", "archive-filter");
  filterBar.setAttribute("role", "group");
  filterBar.setAttribute("aria-label", "Show");
  const stack = el("div", "settings-register-stack");
  const empty = el("p", "empty-state");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(hint, filterBar, stack, empty, error);

  // Survives repaints, so restore/delete keeps the current view.
  let filter: ArchiveFilter = "all";
  let archivedAccounts: AccountView[] = [];
  let projects: ProjectView[] = [];

  const filterButtons = new Map<ArchiveFilter, HTMLButtonElement>();
  for (const key of ["all", "accounts", "projects"] as ArchiveFilter[]) {
    const btn = el("button", "archive-filter-option") as HTMLButtonElement;
    btn.type = "button";
    btn.addEventListener("click", () => {
      filter = key;
      render();
    });
    filterButtons.set(key, btn);
    filterBar.appendChild(btn);
  }

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

    stack.replaceChildren();
    const showAccounts = filter !== "projects" && archivedAccounts.length > 0;
    const showProjects = filter !== "accounts" && projects.length > 0;
    // Section titles only matter when both kinds are listed together.
    const titled = filter === "all";

    empty.hidden = counts[filter] > 0;
    empty.textContent =
      filter === "accounts"
        ? "No archived accounts."
        : filter === "projects"
          ? "No closed projects."
          : "Nothing in the archive.";

    if (showAccounts) {
      if (titled) {
        stack.appendChild(el("h2", "archive-section-title", "Accounts"));
      }
      for (const account of archivedAccounts) {
        const article = el("article", "settings-block");
        article.appendChild(arrangeBlock(accountBlock(account)));
        article.appendChild(
          actionRow(
            async () => {
              await restoreAccount(account.id);
              await paint();
            },
            async () => {
              await deleteAccount(account.id);
              await paint();
            },
            `Permanently delete ${accountWireLabel(account.id)}`,
          ),
        );
        stack.appendChild(article);
      }
    }

    if (showProjects) {
      if (titled) {
        stack.appendChild(el("h2", "archive-section-title", "Projects"));
      }
      for (const project of projects) {
        const article = el("article", "settings-block");
        article.appendChild(arrangeBlock(closedProjectBlock(project)));
        const canRestore = project.cancelled && !project.completed;
        article.appendChild(
          actionRow(
            canRestore
              ? async () => {
                  await restoreProject(project.project_id);
                  await paint();
                }
              : null,
            async () => {
              await deleteProject(project.project_id);
              await paint();
            },
            `Permanently delete project ${project.project_id}`,
          ),
        );
        stack.appendChild(article);
      }
    }

    startAgeClock(host);
  };

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
      stack.replaceChildren();
      empty.hidden = true;
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    }
  };

  await paint();
}
