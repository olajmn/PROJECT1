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
/**
 * `planned: false` skips the planner — `text` becomes the project's
 * name and the tree is built or pasted afterwards.
 */
export async function createGoal(text, simUserId, planned = true) {
    const body = {
        text,
    };
    if (simUserId != null) {
        body.sim_user_id = simUserId;
    }
    if (!planned) {
        body.planned = false;
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
/** macOS folder dialog. Empty string means the user cancelled. */
export async function chooseFolder() {
    const res = await fetch("/api/choose-folder", { method: "POST" });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    const body = (await res.json());
    return body.path ?? "";
}
export async function importProgressionFolder(goalId, folder, parentId) {
    const body = { path: folder };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${goalId}/progression/folder`, {
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
/**
 * Read an existing map back into words — what the project looks to be
 * about. Nothing is saved; the reading is gone on the next render.
 */
export async function readTree(goalId) {
    const res = await fetch(`/api/projects/${goalId}/read`, { method: "POST" });
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
// 2. Simulated users
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
// 4. Model boundary (Settings → General)
export async function fetchModel() {
    const res = await fetch("/api/model");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 5. Sessions (Settings → Logs)
export async function fetchSessions() {
    const res = await fetch("/api/sessions");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
