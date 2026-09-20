// How each paragraph line paints: title / fact / empty.
//
// fact is the general metadata primitive (label → value).

import { AGE_ATTR, formatAge, formatStamp } from "./liveAge.js";
import { el } from "./makeTag.js";
import type { EmptyPara, FactPara, Para, TitlePara } from "./lineKinds.js";

function drawTitle(para: TitlePara): HTMLElement {
  const title = el("p", "settings-title");
  title.appendChild(el("span", "settings-title-kind", para.kind));
  if (para.name) {
    title.appendChild(document.createTextNode(" "));
    title.appendChild(el("span", "settings-title-name", para.name));
  }
  return title;
}

function drawFact(para: FactPara): HTMLElement {
  const row = el("div", "settings-fact");
  row.appendChild(el("span", "settings-fact-label", para.label));
  const value = el("span", "settings-fact-value");

  if (para.created) {
    value.appendChild(el("span", "settings-stamp", formatStamp(para.created)));
    value.appendChild(el("span", "settings-fact-sep", " · "));
    const age = el("span", "settings-age");
    age.setAttribute(AGE_ATTR, para.created);
    age.textContent = formatAge(para.created, Date.now());
    value.appendChild(age);
  } else {
    value.textContent = para.value ?? "—";
  }

  row.appendChild(value);
  return row;
}

function drawEmpty(para: EmptyPara): HTMLElement {
  return el("p", "settings-empty", para.text);
}

/** Paint one paragraph via its `t` kind. */
export function drawLine(para: Para): HTMLElement {
  switch (para.t) {
    case "title":
      return drawTitle(para);
    case "fact":
      return drawFact(para);
    case "empty":
      return drawEmpty(para);
  }
}
