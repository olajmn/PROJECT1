// Settings → Logs page entry.
// Mounts process-session inspect (data/sessions.json).

import { applyStoredTheme } from "../../../user/theme.js";
import { mountLogs } from "./sessions.js";

applyStoredTheme();

const host = document.getElementById("logs");
if (host) {
  void mountLogs(host);
}
