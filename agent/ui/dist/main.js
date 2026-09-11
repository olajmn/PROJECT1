// DOM wiring for the v4 conversation prototype. Deliberately one
// small file: appending chat messages and rendering an optional
// PlanningNode tree are the whole job here - no framework, no state
// library, no routing (see docs/architecture-v4.md, UI Manifestation).
import { sendMessage } from "./api.js";
const transcript = document.getElementById("transcript");
const form = document.getElementById("form");
const input = document.getElementById("input");
function appendMessage(who, text) {
    const row = document.createElement("div");
    row.className = `message message-${who.toLowerCase()}`;
    const label = document.createElement("span");
    label.className = "who";
    label.textContent = who;
    const body = document.createElement("span");
    body.className = "text";
    body.textContent = text;
    row.append(label, body);
    transcript.appendChild(row);
    transcript.scrollTop = transcript.scrollHeight;
}
function renderNode(node) {
    const li = document.createElement("li");
    li.className = `node node-${node.status}`;
    li.textContent = node.label;
    if (node.children.length > 0) {
        const list = document.createElement("ul");
        for (const child of node.children) {
            list.appendChild(renderNode(child));
        }
        li.appendChild(list);
    }
    return li;
}
function appendPlan(node) {
    const wrap = document.createElement("div");
    wrap.className = "plan";
    const list = document.createElement("ul");
    list.appendChild(renderNode(node));
    wrap.appendChild(list);
    transcript.appendChild(wrap);
    transcript.scrollTop = transcript.scrollHeight;
}
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text)
        return;
    appendMessage("You", text);
    input.value = "";
    input.disabled = true;
    try {
        const result = await sendMessage(text);
        appendMessage("Agent", result.reply);
        if (result.node) {
            appendPlan(result.node);
        }
    }
    catch (err) {
        appendMessage("Agent", `(error: ${err.message})`);
    }
    finally {
        input.disabled = false;
        input.focus();
    }
});
input.focus();
