// "Log out" at the foot of the sidebar, next to Settings — only when the
// server runs the public demo (docs/demo.md).

import { logOut } from "../api.js";

export function installLogoutLink(nav: HTMLElement, demo: boolean): void {
  if (!demo) return;
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
