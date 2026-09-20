// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.
async function httpErrorMessage(res) {
    const detail = (await res.text()).trim();
    const fromHtml = detail.match(/Error code: \d+[\s\S]*?<p>([^<]+)/i)?.[1]?.trim() ??
        detail.match(/<p>([^<]+)<\/p>/i)?.[1]?.trim();
    const plain = (fromHtml || detail || `request failed: ${res.status}`).replace(/\s+/g, " ");
    return plain.slice(0, 240);
}
// 1. Goals / Projects
export async function fetchActiveGoals() {
    const res = await fetch("/api/projects");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function createGoal(text, simUserId) {
    const body = { text };
    if (simUserId != null) {
        body.sim_user_id = simUserId;
    }
    const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function sendGoalFeedback(goalId, text, focusLabel, focusStepId) {
    const body = { text };
    if (focusLabel) {
        body.focus_label = focusLabel;
    }
    if (focusStepId) {
        body.focus_step_id = focusStepId;
    }
    const res = await fetch(`/api/projects/${goalId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function cancelGoal(goalId) {
    const res = await fetch(`/api/projects/${goalId}/cancel`, { method: "POST" });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function setProjectUser(goalId, simUserId) {
    const res = await fetch(`/api/projects/${goalId}/user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sim_user_id: simUserId }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function zoomGoalStep(goalId, stepId) {
    const res = await fetch(`/api/projects/${goalId}/zoom/${stepId}`, { method: "POST" });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        // send_error() returns an HTML page; pull the plain reason if present.
        const plain = detail.match(/no timeframe[\s\S]*?(?=<|$)/i)?.[0]
            ?? detail.match(/Error code: (\d+)[\s\S]*?<p>([^<]+)/i)?.[2]
            ?? detail.match(/cannot zoom[^.<]*/i)?.[0];
        throw new Error((plain || detail || `request failed: ${res.status}`).slice(0, 200));
    }
    return (await res.json());
}
export async function addProgressionStep(goalId, label, parentId) {
    const body = { label };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${goalId}/progression`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function importProgressionOutline(goalId, text, parentId, unwrap = true) {
    const body = {
        text,
        unwrap,
    };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${goalId}/progression/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
/** Dry-run parse_outline() both ways (title line dropped / kept) so
 * the paste form can show what would be created before committing -
 * no goal needed, nothing saved. */
export async function previewOutline(text) {
    const res = await fetch("/api/parse-outline-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
/** Import an already-built {"label", "children"} tree directly - no
 * text parsing, no unwrap guess - for when the caller already has the
 * exact shape the user chose (ui/'s preview, after toggling nodes
 * in/out). See import_progression_outline()'s own `forest` param. */
export async function importProgressionForest(goalId, nodes, parentId) {
    const body = { nodes };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${goalId}/progression/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function removeProgressionStep(goalId, stepId) {
    const res = await fetch(`/api/projects/${goalId}/progression/${stepId}/remove`, {
        method: "POST",
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function fetchCompletedGoals() {
    const res = await fetch("/api/projects/completed");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 2. History
export async function fetchHistory() {
    const res = await fetch("/api/history");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 3. Simulated users
export async function fetchUsers() {
    const res = await fetch("/api/users");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function createUser(text) {
    const res = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function archiveUser(simUserId) {
    const res = await fetch(`/api/users/${simUserId}/archive`, { method: "POST" });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 4. Sessions
export async function fetchSessions() {
    const res = await fetch("/api/sessions");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 5. Steps (scratch tree)
/** Whatever tree the server currently holds - `root` is null if none
 * has been built yet, or if the process restarted (it is in memory
 * only). */
export async function fetchTree() {
    const res = await fetch("/api/tree");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
/** Unlike the wrappers above, these surface the server's own reason
 * phrase instead of just the status code - the Steps routes reject
 * text with no timeframe in it (422), and that reason is the whole
 * point of the rejection, not an internal detail. */
async function postTree(path, body) {
    const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(res.statusText || `request failed: ${res.status}`);
    }
    return (await res.json());
}
export function createTree(text) {
    return postTree("/api/tree", { text });
}
export function zoomStep(stepId) {
    return postTree(`/api/tree/${stepId}/zoom`);
}
