// How each register line paints: title / fact / empty.
//
// fact is the general metadata primitive (label → value).

import { AGE_ATTR, formatAge, formatStamp } from "./ageClock.js";
import { el } from "./dom.js";
import type { EmptyLine, FactLine, Line, TitleLine } from "./types.js";

function paintTitle(line: TitleLine): HTMLElement {
  const title = el("p", "settings-title");
  title.appendChild(el("span", "settings-title-kind", line.kind));
  if (line.name) {
    title.appendChild(document.createTextNode(" "));
    title.appendChild(el("span", "settings-title-name", line.name));
  }
  return title;
}

function paintFact(line: FactLine): HTMLElement {
  const row = el("div", "settings-fact");
  row.appendChild(el("span", "settings-fact-label", line.label));
  const value = el("span", "settings-fact-value");

  if (line.created) {
    value.appendChild(el("span", "settings-stamp", formatStamp(line.created)));
    value.appendChild(el("span", "settings-fact-sep", " · "));
    const age = el("span", "settings-age");
    age.setAttribute(AGE_ATTR, line.created);
    age.textContent = formatAge(line.created, Date.now());
    value.appendChild(age);
  } else {
    value.textContent = line.value ?? "—";
  }

  row.appendChild(value);
  return row;
}

function paintEmpty(line: EmptyLine): HTMLElement {
  return el("p", "settings-empty", line.text);
}

/** Paint one line via its `t` kind. */
export function paintLine(line: Line): HTMLElement {
  switch (line.t) {
    case "title":
      return paintTitle(line);
    case "fact":
      return paintFact(line);
    case "empty":
      return paintEmpty(line);
  }
}
