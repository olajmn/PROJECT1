// Foot of the Manager menu: mint a new id#N (optional label).

import { createUser } from "../../api.js";
import { setButtonBusy } from "../../shell/busy.js";
import { setActiveUserId } from "../../user/activeUser.js";
import type { ProjectView, UserView } from "../../types.js";
import { claimUnassigned, showError } from "./helpers.js";

export type CreateIdCallbacks = {
  onUsersChanged: (users: UserView[]) => void;
  onProjectsUpdated: (updated: ProjectView[]) => void;
  onActiveUserChanged: (userId: number | null) => void;
  /** Rebuild menu + brand after a successful mint. */
  afterChange: () => void;
};

export function buildCreateIdForm(
  allUsers: UserView[],
  projects: ProjectView[],
  cb: CreateIdCallbacks,
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
      cb.onUsersChanged([...allUsers, created]);
      if (claimed.length > 0) cb.onProjectsUpdated(claimed);
      setActiveUserId(created.id);
      cb.onActiveUserChanged(created.id);
      cb.afterChange();
    } catch (err) {
      setButtonBusy(button, false);
      input.disabled = false;
      showError(form, err);
    }
  });
  return form;
}
