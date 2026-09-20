// Settings → Directory page entry.
// Mounts the id / project register (shape in spec.ts).

import { mountDirectory } from "./directory.js";

const host = document.getElementById("directory");
if (host) {
  void mountDirectory(host);
}
