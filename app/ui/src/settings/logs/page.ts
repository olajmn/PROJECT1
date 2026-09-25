// Settings → Logs page entry.
// Mounts the activity log (every saved change, newest first).

import { applyStoredTheme } from "../../user/theme.js";
import { mountLogs } from "./activity.js";

applyStoredTheme();

const host = document.getElementById("logs");
if (host) {
  void mountLogs(host);
}
