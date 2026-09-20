// Register visual template — how a Settings register div looks.
//
// Last authoring step before paint: title + fact rows (label → value).
// Shared by General, Directory, and Logs. Edit fact lists here to steer look.

// Contents
//  1. Value bags
//  2. Model block (General)
//  3. Session block (Logs)
//  4. Id group / project / orphan (Directory)

import type { Block, Group } from "./lineKinds.js";

// 1. Value bags

export type ModelValues = {
  model: string;
  provider: string;
  temperature: number;
};

export type SessionValues = {
  id: number;
  startedAt: string;
  current: boolean;
};

export type ProjectValues = {
  id: number;
  goal: string;
  created: string | null | undefined;
};

export type IdValues = {
  id: number;
  label: string;
  created: string;
  active: boolean;
  projects: ProjectValues[];
};

// 2. Model block (General)
//
//   Model  gpt-…
//   Provider      …
//   Temperature   …

export function modelBlock(v: ModelValues): Block {
  return [
    { t: "title", kind: "Model", name: v.model },
    { t: "fact", label: "Provider", value: v.provider },
    { t: "fact", label: "Temperature", value: String(v.temperature) },
  ];
}

// 3. Session block (Logs)
//
//   Session  3
//   ID        3
//   Started   …
//   Status    Current

export function sessionBlock(v: SessionValues): Block {
  return [
    { t: "title", kind: "Session", name: String(v.id) },
    { t: "fact", label: "ID", value: String(v.id) },
    { t: "fact", label: "Started", created: v.startedAt },
    { t: "fact", label: "Status", value: v.current ? "Current" : "—" },
  ];
}

// 4. Id group / project / orphan (Directory)
//
//   Id
//   Name      ai_slop
//   ID        1
//   Created   …
//
//                     Project
//                     Name      prosjekt-1
//                     ID        1
//                     Created   …

export function idGroup(v: IdValues): Group {
  const left: Block = [
    { t: "title", kind: "Id", name: "" },
    { t: "fact", label: "Name", value: v.label },
    { t: "fact", label: "ID", value: String(v.id) },
    { t: "fact", label: "Created", created: v.created },
  ];
  return {
    active: v.active,
    dataSimUserId: String(v.id),
    left,
    right: v.projects.map(projectBlock),
  };
}

export function projectBlock(v: ProjectValues): Block {
  return [
    { t: "title", kind: "Project", name: "" },
    { t: "fact", label: "Name", value: v.goal },
    { t: "fact", label: "ID", value: String(v.id) },
    { t: "fact", label: "Created", created: v.created ?? null },
  ];
}

export function orphanGroup(projects: ProjectValues[]): Group {
  return {
    left: [
      { t: "title", kind: "Id", name: "" },
      { t: "fact", label: "Name", value: "Unassigned" },
      { t: "fact", label: "ID", value: "—" },
    ],
    right: projects.map(projectBlock),
  };
}
