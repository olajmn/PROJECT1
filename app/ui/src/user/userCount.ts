// Sets the Users nav link to "Users (N)" — active non-archived count
// (simulated id#N; wire: /api/users). Called once by each page entry.

// Contents
//  1. initUserCount()

import { fetchUsers } from "../api.js";

// 1. initUserCount()

export async function initUserCount(): Promise<void> {
  const userLink = document.querySelector<HTMLAnchorElement>(
    'a[data-nav="users"]',
  );

  try {
    const users = await fetchUsers();
    if (userLink) {
      const n = users.filter((u) => !u.archived).length;
      userLink.textContent = `Users (${n})`;
    }
  } catch {
    // Leave the plain labels already in the HTML.
  }
}
