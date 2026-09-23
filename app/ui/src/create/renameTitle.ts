/**
 * Click the map title to rename the project. The map only paints the
 * label; this file owns the edit. Talk chart does not call it.
 */

export type RenameHandler = (name: string) => void | Promise<void>;

export function installTitleRename(
  nameText: HTMLElement,
  storedName: string,
  onRename: RenameHandler,
): void {
  nameText.classList.add("is-renamable");
  nameText.title = "Rename";
  nameText.tabIndex = 0;

  const start = (event: Event): void => {
    event.preventDefault();
    event.stopPropagation();
    if (nameText.parentElement?.querySelector(".progress-name-input")) {
      return;
    }
    openEditor(nameText, storedName, onRename);
  };

  nameText.addEventListener("click", start);
  nameText.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      start(event);
    }
  });
}

function openEditor(
  nameText: HTMLElement,
  storedName: string,
  onRename: RenameHandler,
): void {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "progress-name-input";
  input.value = storedName;
  input.setAttribute("aria-label", "Project name");
  nameText.replaceWith(input);
  input.focus();
  input.select();

  let closed = false;
  const restore = (): void => {
    if (input.parentElement) {
      input.replaceWith(nameText);
    }
  };
  const finish = (save: boolean): void => {
    if (closed) return;
    closed = true;
    const next = input.value.trim();
    if (!save || !next || next === storedName) {
      restore();
      return;
    }
    void Promise.resolve(onRename(next)).catch(() => {
      restore();
    });
  };

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      input.blur();
      finish(true);
    } else if (event.key === "Escape") {
      event.preventDefault();
      finish(false);
    }
  });
  input.addEventListener("blur", () => finish(true));
  input.addEventListener("pointerdown", (event) => {
    event.stopPropagation();
  });
}
