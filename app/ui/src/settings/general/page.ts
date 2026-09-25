// Settings → General page entry.
// Appearance (theme) + About-style model facts.

import { applyStoredTheme } from "../../user/theme.js";
import { mountAppearance } from "./appearance.js";
import { mountModelFacts } from "./modelFacts.js";

applyStoredTheme();

const appearance = document.getElementById("appearance");
if (appearance) mountAppearance(appearance);

const host = document.getElementById("model-facts");
if (host) {
  void mountModelFacts(host);
}
