// One-line templates: title / meta / fact / empty.

import { AGE_ATTR, formatAge, formatStamp } from "./ageClock.js";
import { el } from "./dom.js";
import type { EmptyPara, FactPara, MetaPara, Para, TitlePara } from "./types.js";

function renderTitle(para: TitlePara): HTMLElement {
  const title = el("p", "settings-title");
  title.appendChild(el("span", "settings-title-kind", para.kind));
  title.appendChild(document.createTextNode(" "));
  title.appendChild(el("span", "settings-title-name", para.name));
  if (para.badge) {
    title.appendChild(el("span", "settings-badge", para.badge));
  }
  return title;
}

function renderMeta(para: MetaPara): HTMLElement {
  const line = el("p", "settings-meta");
  for (const part of para.parts) {
    if (line.childNodes.length > 0) {
      line.appendChild(el("span", "settings-meta-sep", " · "));
    }
    line.appendChild(document.createTextNode(part));
  }
  if (line.childNodes.length > 0) {
    line.appendChild(el("span", "settings-meta-sep", " · "));
  }
  line.appendChild(
    el("span", "settings-meta-label", para.createdLabel ?? "Created "),
  );
  const iso = para.created;
  if (!iso) {
    line.appendChild(document.createTextNode("—"));
    return line;
  }
  line.appendChild(el("span", "settings-stamp", formatStamp(iso)));
  line.appendChild(el("span", "settings-meta-sep", " · "));
  const age = el("span", "settings-age");
  age.setAttribute(AGE_ATTR, iso);
  age.textContent = formatAge(iso, Date.now());
  line.appendChild(age);
  return line;
}

function renderFact(para: FactPara): HTMLElement {
  const row = el("div", "settings-fact");
  row.appendChild(el("span", "settings-fact-label", para.label));
  row.appendChild(el("span", "settings-fact-value", para.value));
  return row;
}

function renderEmpty(para: EmptyPara): HTMLElement {
  return el("p", "settings-empty", para.text);
}

/** Paint one paragraph via its `t` template. */
export function renderPara(para: Para): HTMLElement {
  switch (para.t) {
    case "title":
      return renderTitle(para);
    case "meta":
      return renderMeta(para);
    case "fact":
      return renderFact(para);
    case "empty":
      return renderEmpty(para);
  }
}
