/**
 * Paste a tree into the Projects map: textarea, live preview with
 * per-node exclude toggles, Import / Cancel.
 */
import { importProgressionForest, importProgressionOutline, previewOutline, } from "../api.js";
export function toPreviewNode(node, excluded) {
    return {
        label: node.label,
        children: node.children.map((c) => toPreviewNode(c, false)),
        excluded,
    };
}
/** An excluded node drops out, but its children are promoted. */
export function applyExclusions(nodes) {
    const result = [];
    for (const node of nodes) {
        const children = applyExclusions(node.children);
        if (node.excluded) {
            result.push(...children);
        }
        else {
            result.push({ label: node.label, children });
        }
    }
    return result;
}
export function previewTreeElement(nodes, onToggle) {
    const list = document.createElement("ul");
    list.className = "outline-preview-list";
    for (const node of nodes) {
        const item = document.createElement("li");
        const label = document.createElement("span");
        label.className = "outline-preview-title-toggle";
        label.classList.toggle("is-excluded", node.excluded);
        label.textContent = node.label;
        label.title = node.excluded
            ? "Click to keep this as its own node"
            : "Click to drop this as its own node (its children still import)";
        label.addEventListener("click", () => onToggle(node));
        item.appendChild(label);
        if (node.children.length > 0) {
            item.appendChild(previewTreeElement(node.children, onToggle));
        }
        list.appendChild(item);
    }
    return list;
}
/**
 * Build the Paste structure button + form. Callers wire the button into
 * the map chrome and append the form under the map.
 */
export function buildPasteTreePanel(opts) {
    const pasteBtn = document.createElement("button");
    pasteBtn.type = "button";
    pasteBtn.className = "map-copy-button";
    pasteBtn.textContent = "Paste structure";
    pasteBtn.title =
        "Import an outline or ASCII tree (e.g. from another LLM) as steps";
    const pasteForm = document.createElement("form");
    pasteForm.className = "map-paste-form";
    pasteForm.hidden = true;
    const pasteInput = document.createElement("textarea");
    pasteInput.className = "map-paste-input";
    pasteInput.placeholder = "Paste an outline or ASCII tree…";
    pasteInput.rows = 6;
    const pasteHint = document.createElement("p");
    pasteHint.className = "map-paste-hint";
    const updatePasteHint = () => {
        const label = opts.getParentLabel();
        pasteHint.textContent = label
            ? `Will import under: ${label}`
            : "Will import at the project root.";
    };
    updatePasteHint();
    const previewBox = document.createElement("div");
    previewBox.className = "map-paste-preview";
    const previewEmpty = document.createElement("p");
    previewEmpty.className = "map-paste-preview-empty";
    previewEmpty.textContent = "Preview appears here as you type or paste.";
    previewBox.appendChild(previewEmpty);
    const pasteActions = document.createElement("div");
    pasteActions.className = "map-paste-actions";
    const pasteSubmit = document.createElement("button");
    pasteSubmit.type = "submit";
    pasteSubmit.textContent = "Import";
    const pasteCancel = document.createElement("button");
    pasteCancel.type = "button";
    pasteCancel.textContent = "Cancel";
    const pasteError = document.createElement("p");
    pasteError.className = "error";
    pasteError.hidden = true;
    pasteActions.append(pasteSubmit, pasteCancel);
    pasteForm.append(pasteInput, pasteHint, previewBox, pasteActions, pasteError);
    let workingTree = null;
    let previewSeq = 0;
    const renderPreview = () => {
        previewBox.innerHTML = "";
        if (!workingTree) {
            previewBox.appendChild(previewEmpty);
            return;
        }
        if (applyExclusions(workingTree).length === 0) {
            const none = document.createElement("p");
            none.className = "map-paste-preview-empty";
            none.textContent = "(nothing recognizable yet)";
            previewBox.appendChild(none);
            return;
        }
        previewBox.appendChild(previewTreeElement(workingTree, (node) => {
            node.excluded = !node.excluded;
            renderPreview();
        }));
    };
    let previewTimer;
    const schedulePreview = () => {
        window.clearTimeout(previewTimer);
        const text = pasteInput.value.trim();
        if (!text) {
            workingTree = null;
            renderPreview();
            return;
        }
        previewTimer = window.setTimeout(async () => {
            const seq = ++previewSeq;
            try {
                const preview = await previewOutline(text);
                if (seq !== previewSeq)
                    return;
                const droppableRoot = preview.kept.length === 1 && preview.kept[0].children.length > 0
                    ? preview.kept[0]
                    : null;
                workingTree = droppableRoot
                    ? [toPreviewNode(droppableRoot, true)]
                    : preview.kept.map((n) => toPreviewNode(n, false));
                renderPreview();
            }
            catch {
                if (seq !== previewSeq)
                    return;
                workingTree = null;
                renderPreview();
            }
        }, 300);
    };
    pasteInput.addEventListener("input", schedulePreview);
    const open = () => {
        pasteForm.hidden = false;
        updatePasteHint();
        pasteForm.scrollIntoView({ behavior: "smooth", block: "nearest" });
        pasteInput.focus();
    };
    pasteBtn.addEventListener("click", () => {
        pasteForm.hidden = !pasteForm.hidden;
        if (!pasteForm.hidden) {
            updatePasteHint();
            pasteInput.focus();
        }
    });
    pasteCancel.addEventListener("click", () => {
        pasteForm.hidden = true;
        pasteInput.value = "";
        pasteError.hidden = true;
        workingTree = null;
        renderPreview();
    });
    pasteForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = pasteInput.value.trim();
        if (!text)
            return;
        pasteError.hidden = true;
        pasteSubmit.disabled = true;
        const parentId = opts.getParentId() ?? undefined;
        try {
            const updated = workingTree
                ? await importProgressionForest(opts.getGoalId(), applyExclusions(workingTree), parentId)
                : await importProgressionOutline(opts.getGoalId(), text, parentId);
            pasteInput.value = "";
            pasteForm.hidden = true;
            workingTree = null;
            opts.onImported(updated);
        }
        catch (err) {
            pasteError.hidden = false;
            pasteError.textContent = `(error: ${err.message})`;
        }
        finally {
            pasteSubmit.disabled = false;
        }
    });
    return {
        pasteBtn,
        pasteForm,
        updatePasteHint,
        isOpen: () => !pasteForm.hidden,
        open,
    };
}
