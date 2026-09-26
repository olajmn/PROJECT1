// Settings → Archive page entry.

import { applyStoredTheme } from "../../user/theme.js";
import { mountArchive } from "./archive.js";

applyStoredTheme();

const host = document.getElementById("archive");
if (host) {
  void mountArchive(host);
}
