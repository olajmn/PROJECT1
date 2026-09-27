// ⋯ menu "Save as tree": store the node's subtree in the account's
// saved-tree library (backend project/saved_trees/). Only structure is
// kept — the nodes on the map are not linked to it afterwards.

import { saveTree } from "../../../api.js";
import type { NodeMenuContext } from "../nodeMenu.js";

export async function saveTreeFromNode(
  stepId: string,
  label: string,
  ctx: NodeMenuContext,
): Promise<void> {
  try {
    const saved = await saveTree(ctx.project.project_id, stepId);
    const nodes = saved.node_count === 1 ? "1 node" : `${saved.node_count} nodes`;
    ctx.markSelected(stepId, `Saved "${saved.name}" as a tree (${nodes}).`);
  } catch (err) {
    ctx.markSelected(stepId, `Could not save "${label}": ${(err as Error).message}`);
  }
}
