// Foot of the Manager menu: mint a new id#N — one click, no typing;
// rename is a separate, not-yet-built feature (see userLabel()'s own
// "user" → id#N fallback, unchanged here).

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

export function buildCreateIdButton(
  allUsers: UserView[],
  projects: ProjectView[],
  cb: CreateIdCallbacks,
): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "sidebar-add sidebar-id-menu-create";
  button.title = "Create id";
  button.setAttribute("aria-label", "Create id");
  button.textContent = "+";
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    setButtonBusy(button, true);
    try {
      const created = await createUser("user");
      const claimed = await claimUnassigned(created.id, projects);
      cb.onUsersChanged([...allUsers, created]);
      if (claimed.length > 0) cb.onProjectsUpdated(claimed);
      setActiveUserId(created.id);
      cb.onActiveUserChanged(created.id);
      cb.afterChange();
    } catch (err) {
      setButtonBusy(button, false);
      showError(button.parentElement ?? button, err);
    }
  });
  return button;
}
