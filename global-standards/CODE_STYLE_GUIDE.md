# Code Style Guide

A reusable standard for how AI-generated source code should be structured, organized, and presented so it remains understandable, navigable, and maintainable for a human developer. This file is project-independent and can be copied into any software project or provided to any AI assistant (Claude, ChatGPT, or others) as a reference for code structure.

## How to use this guide

Provide this file as context when an AI assistant creates or updates source code files. It complements `DOCUMENTATION_STYLE_GUIDE.md` — that guide governs *documentation* (README files, architecture notes, specs); this guide governs *source code files themselves*.

## Scope

This guide governs **source code files themselves** — how an AI assistant structures, organizes, and makes larger code files navigable for humans. This includes Contents/file index blocks, logical sections within a file, and the placement of classes and functions.

It does not govern how README files, architecture documents, requirements, implementation plans, or other written project documentation is written. For those rules, see `DOCUMENTATION_STYLE_GUIDE.md`.

This guide is deliberately not a general coding-style manual — it does not define indentation, semicolons, line length, or preferred syntax. It covers only what affects whether a human can understand, navigate, and maintain the code.

## Contents

1. Contents / File Index
2. Code Organization
3. Naming
4. Comments
5. Consistency and Change Management
6. Avoid Overengineering
7. AI-Specific Behavior

## 1. Contents / File Index

Large or structurally complex source files should include a short Contents block, in a comment, near the top of the file — a map of what the file contains, not a description of what it does.

Unlike Markdown headings, plain code comments are not auto-outlined by editors or version-control viewers: a `// 1. Setup` comment is just text to the tool, not a navigable heading. This is why a hand-written Contents block earns its place in source files, even where the equivalent is often optional in Markdown documentation (see `DOCUMENTATION_STYLE_GUIDE.md` §10, Contents).

- Place it near the top of the file, typically inside the file's header comment or docstring.
- Show the file's actual structure, in its actual order — its major logical sections, and, beneath each, the important classes, functions, methods, or event handlers it contains.
- Do not list every variable, statement, or trivial helper.
- Do not add this to small or simple files where it provides no real navigational value.
- Keep it synchronized with the actual code — update it when sections, classes, or functions are added, removed, renamed, or reorganized.
- **Code structure comes first; the Contents block reflects it — never the other way around.** If a file naturally has three logical sections, the Contents shows three. Do not reorganize code, or invent extra sections, just to make the Contents block look more complete.

A Contents block is a map, not documentation — it shows *where* something is, not *what it does* or *how it works*. That belongs in code comments or in `DOCUMENTATION_STYLE_GUIDE.md`-governed documentation instead.

Useful:
```text
3. API Functions
   - fetchData()
   - postData()
```

Not the intent:
```text
3. API Functions
   - fetchData() retrieves records from the API, converts the JSON
     response into objects, and stores them in application state...
```

Example:

```javascript
/*
 * Contents
 *
 * 1. Imports and Configuration
 *
 * 2. Classes
 *    - BaseEntity
 *    - SubTypeA
 *    - SubTypeB
 *
 * 3. API Functions
 *    - fetchData()
 *    - postData()
 *
 * 4. Validation
 *    - validateInput()
 *
 * 5. Notifications
 *    - notifyOverdue()
 *
 * 6. UI Rendering
 *    - renderList()
 *    - renderBoard()
 *
 * 7. Event Listeners
 *
 * 8. Initialization
 */
```

## 2. Code Organization

- Group related functionality together; avoid scattering the same kind of logic throughout a file.
- Prefer a logical top-to-bottom structure that another developer can follow without jumping around.
- Keep genuinely distinct concerns — for example, data/API access, UI rendering, and core business/model logic — from blending together unnecessarily. This can mean separate files, or simply separate, clearly labeled sections within one file (see §1, Contents/File Index) when the project requires everything in a single file.
- This is a goal, not a rigid rule, and not a mandate for extra files or layers — apply it only as far as the project's actual size and requirements call for.

Where a file has real internal depth, this grouping forms a hierarchy:

Source File → Major Section → Structural Unit → Sub-unit → Details

- A **major section** groups a distinct concern (see above) and matches the top level of the Contents block (§1).
- A **structural unit** — a class, or a top-level function/handler within that section — is normally the deepest level worth naming in the Contents block.
- A **sub-unit** (a method, a nested helper) and **details** (statements, trivial helpers) are part of the code itself and do not need a separate mention in Contents unless individually significant enough to be a navigation target.

This mirrors `DOCUMENTATION_STYLE_GUIDE.md`'s Document Structure principle, applied to code — not a requirement that every file use all four levels. A short file may only have a Major Section and a Structural Unit; collapse whatever levels the file doesn't need.

## 3. Naming

- Use descriptive names for classes, functions, and variables — names should make the code easier to navigate, not just shorter to type.
- Follow the project's existing naming conventions rather than introducing a new pattern partway through.
- Keep names in the Contents block (§1) matching the actual code exactly — an outdated or approximate name in Contents defeats its purpose as a map.

## 4. Comments

Comments should explain **why**, not repeat **what** the code already makes obvious.

- Use comments for non-obvious logic, constraints, workarounds, or design decisions — not to narrate every line.
- If a comment would only restate what the code already says, it is not needed.

## 5. Consistency and Change Management

When a source file changes:

- Update its Contents block (§1) if the file's structure changes.
- Update or remove comments that become outdated — do not leave a comment describing behavior that no longer exists.
- Respect the file's existing structure and conventions before introducing a new pattern; do not restructure code that already works just to match a different style.

This mirrors `DOCUMENTATION_STYLE_GUIDE.md` §6 (Consistency), applied to source code.

## 6. Avoid Overengineering

Do not introduce, unprompted:

- Unnecessary abstractions or design patterns
- Unnecessary classes, files, libraries, or frameworks
- Additional architectural layers

Complexity should be justified by the project's actual requirements, not added because a more sophisticated solution is technically possible.

## 7. AI-Specific Behavior

- Do not assume something exists in the project unless it has been confirmed.
- Do not change existing architecture or code structure without a clear reason.
- Do not create new files without an actual need for them.
- Do not rewrite working code merely to make it "cleaner."
- Flag uncertainty rather than inventing a solution.

**Existing project requirements and established project architecture take precedence over the general preferences in this guide.**
