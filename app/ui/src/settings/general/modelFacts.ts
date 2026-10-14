// General — Model: which model answers in the chat, read from the server.

import { fetchModel } from "../../api.js";
import { settingsError, settingsGroup, settingsRow, settingsSection } from "../rows.js";

/** Fill `#model-facts` with the model, provider, and temperature. */
export async function mountModelFacts(host: HTMLElement): Promise<void> {
  try {
    const info = await fetchModel();
    host.replaceChildren(
      settingsSection(
        "Model",
        settingsGroup([
          settingsRow("Model", info.model),
          settingsRow("Provider", info.provider),
          settingsRow("Temperature", String(info.temperature)),
        ]),
      ),
    );
  } catch (err) {
    host.replaceChildren(settingsError((err as Error).message));
  }
}
