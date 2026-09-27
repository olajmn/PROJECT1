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
// 1. Projects
export async function fetchProjects() {
    const res = await fetch("/api/projects");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
/** Mint a project: `text` is the name, canvas starts empty. */
export async function createProject(text, accountId) {
    const body = {
        text,
    };
    if (accountId != null) {
        body.account_id = accountId;
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
/** Replace the project's display name. Identity stays project_id. */
export async function renameProject(projectId, text) {
    const res = await fetch(`/api/projects/${projectId}/name`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function archiveProject(projectId) {
    const res = await fetch(`/api/projects/${projectId}/cancel`, { method: "POST" });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function fetchArchivedProjects() {
    const res = await fetch("/api/projects/archived");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function restoreProject(projectId) {
    const res = await fetch(`/api/projects/${projectId}/restore`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function deleteProject(projectId) {
    const res = await fetch(`/api/projects/${projectId}/delete`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
}
export async function setProjectUser(projectId, accountId) {
    const res = await fetch(`/api/projects/${projectId}/user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: accountId }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
// 2. Map
export async function addNode(projectId, label, parentId) {
    const body = { label };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${projectId}/map`, {
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
export async function removeNode(projectId, stepId) {
    const res = await fetch(`/api/projects/${projectId}/map/${stepId}/remove`, {
        method: "POST",
    });
    if (!res.ok) {
        const detail = (await res.text()).trim();
        throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function suggestChildren(projectId, stepId) {
    const res = await fetch(`/api/projects/${projectId}/suggest/${stepId}`, { method: "POST" });
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
export async function pasteText(projectId, text, parentId, unwrap = true) {
    const body = {
        text,
        unwrap,
    };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${projectId}/map/import`, {
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
 * no project needed, nothing saved. */
export async function previewPaste(text) {
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
 * in/out). See import_map_outline()'s own `forest` param. */
export async function pasteNodes(projectId, nodes, parentId) {
    const body = { nodes };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${projectId}/map/import`, {
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
export async function addFolder(projectId, folder, parentId) {
    const body = { path: folder };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${projectId}/map/folder`, {
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
// 3. Chat
export async function sendChatMessage(projectId, text, focusLabel, focusStepId) {
    const body = { text };
    if (focusLabel) {
        body.focus_label = focusLabel;
    }
    if (focusStepId) {
        body.focus_step_id = focusStepId;
    }
    const res = await fetch(`/api/projects/${projectId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 4. Accounts
export async function fetchAccounts() {
    const res = await fetch("/api/accounts");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function createAccount(text) {
    const res = await fetch("/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function renameAccount(accountId, text) {
    const res = await fetch(`/api/accounts/${accountId}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function archiveAccount(accountId) {
    const res = await fetch(`/api/accounts/${accountId}/archive`, { method: "POST" });
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
export async function restoreAccount(accountId) {
    const res = await fetch(`/api/accounts/${accountId}/restore`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function deleteAccount(accountId) {
    const res = await fetch(`/api/accounts/${accountId}/delete`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
// 5. Model (Settings → General)
export async function fetchModel() {
    const res = await fetch("/api/model");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
// 6. Activity log (Settings → Logs)
export async function fetchLog() {
    const res = await fetch("/api/log");
    if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
    }
    return (await res.json());
}
/** One project's full history, oldest first (ungrouped). */
export async function fetchProjectTimeline(projectId) {
    const res = await fetch(`/api/projects/${projectId}/timeline`);
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
// 7. Saved trees
/** Store this node and everything under it as structure (no ids). */
export async function saveTree(projectId, stepId) {
    const res = await fetch(`/api/projects/${projectId}/map/${encodeURIComponent(stepId)}/save-tree`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
/** The saved trees of this project's account, newest first. */
export async function fetchSavedTrees(projectId) {
    const res = await fetch(`/api/projects/${projectId}/saved-trees`);
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
/** Insert a saved tree as new nodes (fresh ids) under `parentId`, or
 *  at the top level when it is null. */
export async function insertSavedTree(projectId, treeId, parentId) {
    const body = { tree_id: treeId };
    if (parentId) {
        body.parent_id = parentId;
    }
    const res = await fetch(`/api/projects/${projectId}/map/insert-tree`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
    return (await res.json());
}
export async function deleteSavedTree(treeId) {
    const res = await fetch(`/api/saved-trees/${encodeURIComponent(treeId)}/delete`, { method: "POST" });
    if (!res.ok) {
        throw new Error(await httpErrorMessage(res));
    }
}
