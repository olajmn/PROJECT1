# Content Hierarchy

A reusable, optional convention for labeling hierarchical content in Markdown documents: `1.` → `i.` → `a.`, with matching indentation. This file is project-independent and can be copied into any software project, alongside or independently of `DOCUMENTATION_STYLE_GUIDE.md` and `CODE_STYLE_GUIDE.md`.

## How to use this guide

`DOCUMENTATION_STYLE_GUIDE.md` §10 (Document Structure) establishes that documents should be organized as a hierarchy, but deliberately leaves the choice of labeling notation open — "a project decision." This file is one such decision, packaged as a standalone, adoptable module. A project that wants a consistent, concrete labeling scheme can include this file; a project that doesn't need one can skip it without losing anything from the other two guides.

## Scope

This guide governs **the notation used when a document's heading hierarchy is labeled** — which symbols to use at each level, and how to indent them. It does not govern whether a document should be labeled at all, how deep its hierarchy should go, or which level (if any) serves as a document's citation identity — those remain governed by `DOCUMENTATION_STYLE_GUIDE.md` §10 and §11.

Not every document needs every level, and not every document needs labels at all. `DOCUMENTATION_STYLE_GUIDE.md` §10's existing rules still govern that: collapse levels the content doesn't need, and only label the level that actually serves as the document's citation unit (§10, last paragraph). A document that already has a separate, flat item-numbering series serving as its citation unit is not required to adopt this notation on its headings too — this file fixes *which symbols* to use once a document's structure is being labeled, not *whether* it should be.

It does not apply to code-file Contents blocks — those follow `CODE_STYLE_GUIDE.md` §1, and any project-specific refinement of it.

This is one specific, reusable convention among several equally valid ones (e.g. `1.` → `1.1` → `1.1.1`, or no labels at all) — adopting it, like adopting this file at all, is optional, per project.

## Convention

| Level | Label |
|---|---|
| 1 — Major Section | `1.`, `2.`, `3.` |
| 2 — Subsection | `i.`, `ii.`, `iii.` |
| 3 — further subdivision | `a.`, `b.`, `c.` |

Each level's labels restart under every new parent — the `i.` under section "1." and the `i.` under section "2." are different, unrelated subsections. A label identifies a sibling's position within its own parent, not a position in some global sequence (see `DOCUMENTATION_STYLE_GUIDE.md` §10). Alternating symbol types per level (digits, then roman numerals, then letters) means a label's depth is identifiable on sight, without counting indentation.

Indent nested content by a fixed 3 spaces per level, regardless of label width, so sibling groups line up consistently even though `i.` / `ii.` / `iii.` differ in length:

```text
1. General Principles
   i. Purpose
      a. Scope
      b. Requirements
   ii. Responsibilities
      a. Staff
      b. System
2. Documentation Structure
   i. Headings
      a. Heading Levels
      b. Heading Naming
   ii. Lists
```

The same hierarchy in Markdown headings — Level 1 → `##`, Level 2 → `###`, Level 3 → `####` (the document title stays a bare, unlabeled `#`):

```markdown
## 1. General Principles

### i. Purpose

#### a. Scope

#### b. Requirements

### ii. Responsibilities

#### a. Staff

#### b. System

## 2. Documentation Structure

### i. Headings

#### a. Heading Levels

#### b. Heading Naming

### ii. Lists
```

## Contents

When a document following this convention has a `## Contents` block, its entries reuse the same `1. → i. → a.` labels as the body headings — the labels are the document's citation identity in that case, so Contents can reuse them directly. This differs from a document that already has a separate, flat item-numbering series as its citation unit: there, per `DOCUMENTATION_STYLE_GUIDE.md` §10, only one of the two should carry numbers, so headings and Contents stay unlabeled by design instead.
