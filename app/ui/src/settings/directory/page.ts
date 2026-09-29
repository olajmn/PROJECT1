// Settings → Directory page entry.
// Mounts the accounts and their projects (directory.ts).

import { applyStoredTheme } from "../../user/theme.js";
import { mountDirectory } from "./directory.js";

applyStoredTheme();

const host = document.getElementById("directory");
if (host) {
  void mountDirectory(host);
}
