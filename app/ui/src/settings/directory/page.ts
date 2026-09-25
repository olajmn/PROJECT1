// Settings → Directory page entry.
// Mounts the id / project register (shape in spec.ts).

import { applyStoredTheme } from "../../user/theme.js";
import { mountDirectory } from "./directory.js";

applyStoredTheme();

const host = document.getElementById("directory");
if (host) {
  void mountDirectory(host);
}
