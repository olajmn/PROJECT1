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

Source files whose structure isn't obvious at a glance should include a short Contents block, in a comment, near the top of the file — a map of what the file contains, not a description of what it does. This is common in large files, but the criterion is navigational value, not length itself.

This is a different thing from a document's table of contents. A document-oriented Contents section can naturally live inside a module's or file's own descriptive documentation, as part of that prose (see `DOCUMENTATION_STYLE_GUIDE.md` §11). The source-code Contents convention defined here is not that — it is a structural navigation layer placed near the top of the file, outside the module docstring where appropriate, so a developer can understand the file's architecture at a glance and use it for orientation while scanning or scrolling through the source, distinct from the file's own descriptive header text.

Unlike Markdown headings, plain code comments are not auto-outlined by editors or version-control viewers: a `// 1. Setup` comment is just text to the tool, not a navigable heading. This is why a hand-written Contents block earns its place in source files, even where the equivalent is often optional in Markdown documentation (see `DOCUMENTATION_STYLE_GUIDE.md` §10, Contents).

- Place it near the top of the file, as a comment — outside the module docstring where appropriate, so it reads as a distinct navigation layer rather than part of the file's descriptive text.
- Show the file's actual structure, in its actual order — its major logical sections, and, beneath each, its important declarations: classes, functions, methods, event handlers, constants, mappings, or other meaningful module-level elements it contains.
- Number the major sections in Contents to match the numbers used on the corresponding section headings in the file. This lets Contents double as a navigation map: a section number seen while scanning or scrolling through the file identifies where you are against the map at the top.
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
- A **structural unit** — a class, a top-level function/handler, or another significant top-level declaration (e.g. a constant, mapping, or regular expression) within that section — is normally the deepest level worth naming in the Contents block.
- A **sub-unit** (a method, a nested helper) and **details** (statements, trivial helpers) are part of the code itself and do not need a separate mention in Contents unless individually significant enough to be a navigation target.

This mirrors `DOCUMENTATION_STYLE_GUIDE.md`'s Document Structure principle, applied to code — not a requirement that every file use all four levels. A short file may only have a Major Section and a Structural Unit; collapse whatever levels the file doesn't need.

A file's own opening docstring should be brief: state what the file is responsible for, not a tutorial, a full history, or an architecture explanation that already lives in project documentation. A short pointer to where that fuller context lives is enough.

## 3. Naming

- Use descriptive names for classes, functions, and variables — names should make the code easier to navigate, not just shorter to type.
- Follow the project's existing naming conventions rather than introducing a new pattern partway through.
- Keep names in the Contents block (§1) matching the actual code exactly — an outdated or approximate name in Contents defeats its purpose as a map.

## 4. Comments

Comments should explain **why**, not repeat **what** the code already makes obvious.

- Use comments for non-obvious logic, constraints, workarounds, or design decisions — not to narrate every line.
- If a comment would only restate what the code already says, it is not needed.
- A function or method docstring should document what a caller needs to know that isn't obvious from its name, signature, or body — a real contract, invariant, or non-obvious design choice. It should not restate the function's name in sentence form.
- Keeping a comment because it happens to contain true information is not enough — ask whether that information is actually needed to understand or safely change *this* piece of code. If the same information already lives in project documentation, a short pointer there is usually better than repeating it.
- Removing restatement, repetition, and narrated history is not the same as removing real reasoning — a comment explaining an actual architectural or domain-specific "why" earns its place regardless of length.
- There is no target ratio of comments to code. A section of simple, self-explanatory code needs little or none; a section implementing genuinely difficult logic may legitimately need substantial explanation. Judge each comment on whether it contributes information, not against a percentage.

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
- Do not add headings, a Contents block, comments, or new files for the sake of visible structure — each should exist only because it gives a real reader navigation or understanding value.
- Treat an already-clean file as a legitimate target picture, not a problem to fix — do not edit it just to match this guide's patterns mechanically if it already satisfies their intent.
- Flag uncertainty rather than inventing a solution.

Before creating or substantially editing a source file, briefly weigh — not as a checklist every file must satisfy, but as the judgment call that decides how much structure and documentation this particular file actually needs:

1. How large or complex is this file actually?
2. Does it need a Contents block, or would one add structure without navigation value?
3. What is this file's actual responsibility, in one or two sentences?
4. Which design choices in it are not obvious, and deserve a comment or docstring?
5. What can be left undocumented because the code already expresses it clearly?
6. Does this information already exist elsewhere in the project's documentation, such that a short pointer is enough?

**Existing project requirements and established project architecture take precedence over the general preferences in this guide.**
