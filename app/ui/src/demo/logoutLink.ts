// "Log out" at the foot of the sidebar, next to Settings — only when the
// server runs the public demo (docs/demo.md).

import { fetchSession, logOut } from "../api.js";

export async function installLogoutLink(nav: HTMLElement): Promise<void> {
  try {
    if (!(await fetchSession()).demo) return;
  } catch {
    return;
  }
  const link = document.createElement("a");
  link.href = "/login.html";
  link.textContent = "Log out";
  link.addEventListener("click", async (event) => {
    event.preventDefault();
    await logOut();
    window.location.assign("/login.html");
  });
  nav.appendChild(link);
}
