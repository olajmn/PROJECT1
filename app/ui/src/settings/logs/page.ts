// Settings → Logs page entry.
// Scope: all activity (newest first) or one project's full timeline
// (oldest first, ungrouped).

import { applyStoredTheme } from "../../user/theme.js";
import { mountLogs } from "./activity.js";
import { mountProjectTimeline } from "./projectTimeline.js";
import { mountLogScope, type LogScope } from "./scope.js";

applyStoredTheme();

const scopeHost = document.getElementById("logs-scope");
const listHost = document.getElementById("logs");

function show(scope: LogScope): void {
  if (!listHost) return;
  if (scope.kind === "all") {
    void mountLogs(listHost);
  } else {
    void mountProjectTimeline(listHost, scope.projectId);
  }
}

if (scopeHost && listHost) {
  void mountLogScope(scopeHost, show).then(show);
} else if (listHost) {
  void mountLogs(listHost);
}
