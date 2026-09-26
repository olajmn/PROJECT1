/**
 * Mint a project from one folder on disk.
 *
 * Same walk as the map's Add folder (`canvas/folderForm.ts` →
 * `addFolder`): empty project first, then the folder
 * as root beads. Cancelled picker creates nothing.
 */

import {
  chooseFolder,
  createProject,
  addFolder,
} from "../../api.js";
import type { ProjectView } from "../../dataShapes.js";

export async function mintFromFolder(opts: {
  typedName: string;
  userId: number;
}): Promise<ProjectView | null> {
  const path = await chooseFolder();
  if (!path) return null;

  // Empty falls through to the server's `New project N`.
  const name = opts.typedName.trim() || folderName(path);
  const created = await createProject(name, opts.userId);
  try {
    return await addFolder(created.project_id, path);
  } catch {
    // Project exists; the map's Add folder can retry the walk.
    return created;
  }
}

function folderName(path: string): string {
  const parts = path.replace(/\/+$/, "").split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}
