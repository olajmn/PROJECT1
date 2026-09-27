// Directory — Settings → Directory: account overview, create, rename.
//
// Shape: ../register/blocks.ts

// Contents
//  1. Helpers
//  2. mountDirectory()

import {
  archiveAccount,
  createAccount,
  fetchProjects,
  fetchAccounts,
  renameAccount,
} from "../../api.js";
import { projectsChronologicalForUser } from "../../panes/create/projectOrder.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import {
  accountWireLabel,
  getActiveUserId,
  setActiveUserId,
  userLabel,
} from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import {
  accountGroup,
  arrangeGroup,
  orphanGroup,
  startAgeClock,
  type ProjectValues,
} from "../register/index.js";

// 1. Helpers

function projectValues(project: ProjectView): ProjectValues {
  return {
    id: project.project_id,
    name: project.name,
    created: project.created_at,
    accountN: project.account_n ?? null,
  };
}

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

function editableName(user: AccountView): string {
  const t = user.text?.trim();
  if (t && t !== "user") return t;
  return "";
}

// 2. mountDirectory()

/** Fill a `.settings-register` host from users/projects via directorySpec. */
export async function mountDirectory(host: HTMLElement): Promise<void> {
  host.replaceChildren();

  const create = el("form", "directory-create");
  create.setAttribute("aria-label", "Create account");
  const createLabel = el("label", "directory-create-label", "New account");
  createLabel.htmlFor = "directory-create-name";
  const createInput = el("input", "directory-create-input") as HTMLInputElement;
  createInput.id = "directory-create-name";
  createInput.type = "text";
  createInput.placeholder = "Name (optional — blank → account#N)";
  createInput.autocomplete = "off";
  const createSubmit = el(
    "button",
    "directory-create-submit",
    "Create account",
  ) as HTMLButtonElement;
  createSubmit.type = "submit";
  create.append(createLabel, createInput, createSubmit);

  const hint = el(
    "p",
    "directory-hint",
    "Accounts are created, renamed, and deleted here. The Projects sidebar only switches and lists projects under the active account.",
  );

  const stack = el("div", "settings-register-stack");
  const empty = el("p", "empty-state", "No accounts yet — create one above.");
  empty.hidden = true;
  const error = el("p", "error");
  error.hidden = true;
  host.append(create, hint, stack, empty, error);

  const paint = async (): Promise<void> => {
    stack.replaceChildren();
    error.hidden = true;
    try {
      const [users, projects] = await Promise.all([
        fetchAccounts(),
        fetchProjects(),
      ]);
      const active = users.filter((u) => !u.archived);
      const uiActiveId = getActiveUserId();
      const orphans = projects.filter((p) => p.account_id === null);
      empty.hidden = active.length > 0 || orphans.length > 0;

      for (const user of active) {
        const linked = projectsChronologicalForUser(projects, user.id);
        const article = arrangeGroup(
          accountGroup({
            id: user.id,
            label: userLabel(user),
            created: user.created_at,
            active: uiActiveId === user.id,
            projects: linked.map(projectValues),
          }),
        );
        const actions = el("div", "directory-account-actions");
        const renameBtn = el(
          "button",
          "directory-rename",
          "Rename",
        ) as HTMLButtonElement;
        renameBtn.type = "button";
        renameBtn.title = `Rename ${accountWireLabel(user.id)}`;

        const renameForm = el("form", "directory-rename-form") as HTMLFormElement;
        renameForm.hidden = true;
        renameForm.setAttribute("aria-label", `Rename ${accountWireLabel(user.id)}`);
        const renameInput = el(
          "input",
          "directory-create-input",
        ) as HTMLInputElement;
        renameInput.type = "text";
        renameInput.placeholder = "Name (blank → account#N)";
        renameInput.autocomplete = "off";
        const renameSave = el(
          "button",
          "directory-create-submit",
          "Save",
        ) as HTMLButtonElement;
        renameSave.type = "submit";
        const renameCancel = el(
          "button",
          "directory-rename",
          "Cancel",
        ) as HTMLButtonElement;
        renameCancel.type = "button";
        renameForm.append(renameInput, renameSave, renameCancel);

        renameBtn.addEventListener("click", () => {
          renameBtn.hidden = true;
          renameForm.hidden = false;
          renameInput.value = editableName(user);
          renameInput.focus();
          renameInput.select();
        });
        renameCancel.addEventListener("click", () => {
          renameForm.hidden = true;
          renameBtn.hidden = false;
        });
        renameForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          setButtonBusy(renameSave, true);
          try {
            await renameAccount(user.id, renameInput.value);
            await paint();
          } catch (err) {
            setButtonBusy(renameSave, false);
            error.hidden = false;
            error.textContent = `(error: ${(err as Error).message})`;
          }
        });

        actions.append(renameBtn, renameForm);

        const deleteBtn = el(
          "button",
          "directory-delete",
          "Delete",
        ) as HTMLButtonElement;
        deleteBtn.type = "button";
        deleteBtn.title = `Delete ${accountWireLabel(user.id)} (projects stay)`;

        const deleteConfirm = el("div", "directory-delete-confirm");
        deleteConfirm.hidden = true;
        const deleteNote = el(
          "p",
          "directory-hint",
          "Projects stay; they lose this account link.",
        );
        const deleteYes = el(
          "button",
          "directory-create-submit",
          "Delete account",
        ) as HTMLButtonElement;
        deleteYes.type = "button";
        const deleteNo = el(
          "button",
          "directory-rename",
          "Cancel",
        ) as HTMLButtonElement;
        deleteNo.type = "button";
        deleteConfirm.append(deleteNote, deleteYes, deleteNo);

        deleteBtn.addEventListener("click", () => {
          deleteBtn.hidden = true;
          renameBtn.hidden = true;
          renameForm.hidden = true;
          deleteConfirm.hidden = false;
        });
        deleteNo.addEventListener("click", () => {
          deleteConfirm.hidden = true;
          deleteBtn.hidden = false;
          renameBtn.hidden = false;
        });
        deleteYes.addEventListener("click", async () => {
          setButtonBusy(deleteYes, true);
          try {
            await archiveAccount(user.id);
            if (getActiveUserId() === user.id) {
              const live = (await fetchAccounts()).filter((u) => !u.archived);
              const fallback =
                live.length > 0
                  ? live.reduce((a, b) => (a.id > b.id ? a : b)).id
                  : null;
              setActiveUserId(fallback);
            }
            await paint();
          } catch (err) {
            setButtonBusy(deleteYes, false);
            error.hidden = false;
            error.textContent = `(error: ${(err as Error).message})`;
          }
        });

        actions.append(deleteBtn, deleteConfirm);
        const col = article.querySelector(".settings-col");
        if (col) col.appendChild(actions);
        else article.appendChild(actions);
        stack.appendChild(article);
      }
      if (orphans.length > 0) {
        stack.appendChild(
          arrangeGroup(orphanGroup(orphans.map(projectValues))),
        );
      }
      startAgeClock(host);
    } catch (err) {
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    }
  };

  create.addEventListener("submit", async (event) => {
    event.preventDefault();
    const typed = createInput.value.trim();
    setButtonBusy(createSubmit, true);
    try {
      await createAccount(typed || "user");
      createInput.value = "";
      await paint();
    } catch (err) {
      error.hidden = false;
      error.textContent = `(error: ${(err as Error).message})`;
    } finally {
      setButtonBusy(createSubmit, false);
    }
  });

  await paint();
}
