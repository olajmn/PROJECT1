// Settings → Logs page entry.
// Mounts process-session inspect (data/sessions.json).

import { mountLogs } from "./sessions.js";

const host = document.getElementById("logs");
if (host) {
  void mountLogs(host);
}
