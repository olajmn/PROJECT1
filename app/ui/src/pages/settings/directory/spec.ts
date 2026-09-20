// Directory layout spec — edit to steer Directory.
//
// Shared templates: ../paragraphs.ts (also used by General + Logs).

// Contents
//  1. Value bags
//  2. Id group
//  3. Project block
//  4. Orphan group

import type { Block, Group } from "../paragraphs/index.js";

// 1. Value bags

export type ProjectValues = {
  id: number;
  goal: string;
  sidebar: number;
  created: string | null | undefined;
};

export type IdValues = {
  id: number;
  label: string;
  created: string;
  active: boolean;
  projects: ProjectValues[];
};

// 2. Id group

export function idGroup(v: IdValues): Group {
  return {
    active: v.active,
    dataSimUserId: String(v.id),
    left: [
      {
        t: "title",
        kind: "Id",
        name: v.label,
        badge: v.active ? "Active" : undefined,
      },
      {
        t: "meta",
        parts: [`Id ${v.id}`],
        created: v.created,
      },
    ],
    right: v.projects.map(projectBlock),
  };
}

// 3. Project block

export function projectBlock(v: ProjectValues): Block {
  return [
    {
      t: "title",
      kind: "Project",
      name: v.goal,
    },
    {
      t: "meta",
      parts: [`Id ${v.id}`, `Sidebar #${v.sidebar}`],
      created: v.created,
    },
  ];
}

// 4. Orphan group

export function orphanGroup(projects: ProjectValues[]): Group {
  return {
    left: [
      { t: "title", kind: "Id", name: "Unassigned" },
      { t: "meta", parts: [], created: null },
    ],
    right: projects.map(projectBlock),
  };
}
