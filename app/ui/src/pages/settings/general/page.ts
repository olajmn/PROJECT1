// Settings → General page entry.
// Mounts About-style facts (model first); more can join later.

import { mountModelFacts } from "./modelFacts.js";

const host = document.getElementById("model-facts");
if (host) {
  void mountModelFacts(host);
}
