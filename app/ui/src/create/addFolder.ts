/**
 * Mint a project from one folder on disk.
 *
 * Same walk as the map's Add folder (`map/addFolder.ts` →
 * `importProgressionFolder`): empty project first, then the folder
 * as root beads. Cancelled picker creates nothing.
 */

import {
  chooseFolder,
  createProject,
  importProgressionFolder,
} from "../api.js";
import type { ProjectView } from "../types.js";
import { nextNewProjectName } from "./autoname.js";

export async function mintFromFolder(opts: {
  typedName: string;
  titles: string[];
  userId: number;
}): Promise<ProjectView | null> {
  const path = await chooseFolder();
  if (!path) return null;

  const name =
    opts.typedName.trim() || folderName(path) || nextNewProjectName(opts.titles);
  const created = await createProject(name, opts.userId);
  try {
    return await importProgressionFolder(created.project_id, path);
  } catch {
    // Project exists; the map's Add folder can retry the walk.
    return created;
  }
}

function folderName(path: string): string {
  const parts = path.replace(/\/+$/, "").split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}
