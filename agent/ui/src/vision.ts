// The Vision page - create, list, and archive a Vision (broader,
// cross-goal context a Goal can optionally reference - see
// docs/planning-model.md, the authority on Vision). Deliberately NOT
// yet wired into Set Goal or Active's goal cards - linking a Vision
// to a Goal is its own, separate round, see
// docs/04-current-state.md § 5. This page only manages Visions
// themselves: active and archived shown as two separate sections,
// same split frontend-legacy/templates/vision/page.html already
// established.

import { archiveVision, createVision, fetchVisions } from "./api.js";
import type { VisionView } from "./types.js";

const activeList = document.getElementById("active-visions") as HTMLDivElement;
const archivedList = document.getElementById("archived-visions") as HTMLDivElement;
const emptyActive = document.getElementById("empty-active") as HTMLParagraphElement;
const emptyArchived = document.getElementById("empty-archived") as HTMLParagraphElement;
const form = document.getElementById("form") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;

function renderVisionCard(vision: VisionView): HTMLElement {
  const card = document.createElement("article");
  card.className = "vision-card";

  const header = document.createElement("div");
  header.className = "card-header";
  const text = document.createElement("p");
  text.textContent = vision.text;
  const id = document.createElement("span");
  id.className = "entity-id";
  id.textContent = `#${vision.id}`;
  header.append(text, id);
  card.appendChild(header);

  if (!vision.archived) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Archive";
    button.className = "archive-button";
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await archiveVision(vision.id);
        await loadVisions();
      } catch (err) {
        button.disabled = false;
        const error = document.createElement("p");
        error.className = "error";
        error.textContent = `(error: ${(err as Error).message})`;
        card.appendChild(error);
      }
    });
    card.appendChild(button);
  }

  return card;
}

async function loadVisions(): Promise<void> {
  const visions = await fetchVisions();
  const active = visions.filter((v) => !v.archived);
  const archived = visions.filter((v) => v.archived);

  activeList.innerHTML = "";
  emptyActive.hidden = active.length > 0;
  for (const vision of active) {
    activeList.appendChild(renderVisionCard(vision));
  }

  archivedList.innerHTML = "";
  emptyArchived.hidden = archived.length > 0;
  for (const vision of archived) {
    archivedList.appendChild(renderVisionCard(vision));
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.disabled = true;
  try {
    await createVision(text);
    input.value = "";
    await loadVisions();
  } catch (err) {
    const error = document.createElement("p");
    error.className = "error";
    error.textContent = `(error: ${(err as Error).message})`;
    form.appendChild(error);
  } finally {
    input.disabled = false;
    input.focus();
  }
});

loadVisions().catch((err) => {
  emptyActive.hidden = false;
  emptyActive.textContent = `(error loading visions: ${(err as Error).message})`;
});
