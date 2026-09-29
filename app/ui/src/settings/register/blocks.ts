// Register blocks — how a Settings register entry looks (title + facts).
// Shared by Directory and Logs (General and Archive moved to ../rows.ts; the rest
// follow — TODO.md § Parallel paths). Edit fact lists here to steer look.

// Contents
//  1. Value bags
//  2. Log entry block (Logs)
//  3. Id group / project / orphan (Directory)

import type { Block, Group } from "./types.js";

// 1. Value bags

export type LogValues = {
  kind: string;
  project: string;
  at: string | null;
  text: string;
  focus?: string;
};

export type ProjectValues = {
  id: number;
  name: string;
  created: string | null | undefined;
  /** Sticky per-account mint (`account_n`). */
  accountN?: number | null;
};

export type IdValues = {
  id: number;
  label: string;
  created: string;
  active: boolean;
  projects: ProjectValues[];
};

// 2. Log entry block (Logs)
//
//   Chat  nytt bygg
//   When   …
//   What   whats this about?

export function logBlock(v: LogValues): Block {
  const block: Block = [
    { t: "title", kind: v.kind, name: v.project },
    { t: "fact", label: "When", created: v.at },
  ];
  if (v.text) block.push({ t: "fact", label: "What", value: v.text });
  if (v.focus) block.push({ t: "fact", label: "Focus", value: v.focus });
  return block;
}

// 3. Account group / project / orphan (Directory)
//
//   Account
//   Name      ai_slop
//   Id        account#1
//   Created   …
//
//                     Project
//                     Name       prosjekt-1
//                     Local #    #1
//                     Global ID  49
//                     Created    …

export function accountGroup(v: IdValues): Group {
  const left: Block = [
    { t: "title", kind: "Account", name: "" },
    { t: "fact", label: "Name", value: v.label },
    { t: "fact", label: "Id", value: `account#${v.id}` },
    { t: "fact", label: "Created", created: v.created },
  ];
  return {
    active: v.active,
    dataAccountId: String(v.id),
    left,
    right: v.projects.map(projectBlock),
  };
}


export function projectBlock(v: ProjectValues): Block {
  const local =
    v.accountN != null ? `#${v.accountN}` : "—";
  return [
    { t: "title", kind: "Project", name: "" },
    { t: "fact", label: "Name", value: v.name },
    { t: "fact", label: "Local #", value: local },
    { t: "fact", label: "Global ID", value: String(v.id) },
    { t: "fact", label: "Created", created: v.created ?? null },
  ];
}

export function orphanGroup(projects: ProjectValues[]): Group {
  return {
    left: [
      { t: "title", kind: "Account", name: "" },
      { t: "fact", label: "Name", value: "Unassigned" },
      { t: "fact", label: "Id", value: "—" },
    ],
    right: projects.map(projectBlock),
  };
}
