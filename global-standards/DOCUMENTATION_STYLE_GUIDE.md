# Documentation Style Guide

A reusable standard for how AI-generated project documentation should be written. This file is project-independent and can be copied into any software project or provided to any AI assistant (Claude, ChatGPT, or others) as a reference for documentation style.

## How to use this guide

Provide this file as context when an AI assistant creates or updates project documentation (README files, architecture notes, requirement specs, implementation plans, changelogs, etc.). Everyday conversation between the user and the assistant may happen in any language, but the rules below apply specifically to the documentation output itself.

## Scope

This guide governs **written project documentation** — how an AI assistant writes and structures README files, architecture documents, requirements, implementation plans, technical notes, specifications, changelogs, and similar material.

It does not govern how source code files themselves are organized or structured. Code examples within documentation may follow ordinary code conventions, but this guide does not define how production code should be organized. For rules on structuring and navigating source code, see `CODE_STYLE_GUIDE.md`.

## Contents

1. Written Language
2. Technical Accuracy
3. Technical Writing
4. Describing
5. Facts vs. Assumptions
6. Consistency
7. AI Behavior When Generating Documentation
8. Code References
9. Formatting
10. Document Structure
11. Contents
12. Examples

## 1. Written Language

- All project documentation must be written in English, regardless of the language used in conversation with the AI assistant.
- Use standard English software-development terminology. Do not translate established technical terms.
- Do not mix languages within a documentation file.

## 2. Technical Accuracy

- Use precise, technically correct terminology.
- Do not simplify a concept to the point where the description becomes inaccurate.
- Use the actual names of classes, functions, files, variables, APIs, and technologies used in the project. Do not paraphrase identifiers.
- Do not invent technical details that are not known or supported by the project. If a detail is not confirmed, mark it as an assumption or open question (see §5).

## 3. Technical Writing

Documentation should be clear, concise, structured, technically precise, professional, and objective.

Avoid:
- Marketing language ("powerful", "seamless", "amazing", "cutting-edge")
- Exaggerated claims about ease of use, performance, or quality
- Emotional or persuasive language
- Generic AI-style filler sentences that add no information

Weak:
> "This powerful and amazing feature makes it incredibly easy for users to manage their data."

Better:
> "This feature allows users to create, edit, and delete records through a single form."

## 4. Describing

When documenting a component, feature, architecture decision, or implementation, explain — where relevant:

- **What** it does
- **Why** it exists (the problem it solves)
- **How** it works (at a level appropriate for the audience, not line-by-line)
- **How** it relates to other parts of the system
- Relevant **constraints or dependencies**

Do not explain every trivial implementation detail unless it is relevant to understanding the system. A getter/setter does not need a paragraph; a non-obvious algorithm or design decision does.

## 5. Facts vs. Assumptions

Documentation must clearly distinguish between:

| Category | Meaning |
|---|---|
| Requirement | Something explicitly required by a spec, ticket, or stakeholder |
| Confirmed fact | Something verified in the code, tests, or system behavior |
| Implementation decision | A choice made by the team/developer, with reasoning if non-obvious |
| Assumption | Something believed true but not verified |
| Open question | Something unresolved that needs a decision or clarification |
| Limitation | A known constraint, edge case, or gap in current functionality |

Never present an assumption as an established fact. When uncertain which category something belongs to, label it explicitly rather than omitting the label (e.g., "Assumption: ...", "Open question: ...").

## 6. Consistency

Documentation must remain consistent with the actual project:

- Update affected documentation when the implementation changes.
- Do not leave outdated technical descriptions in place after a change.
- When documentation and code diverge, treat this as a defect to fix, not an acceptable state.

## 7. AI Behavior When Generating Documentation

- Prioritize accuracy over length — do not add information, generic filler, or boilerplate introductions/conclusions merely to make a document appear longer or more complete.
- Preserve the distinction between what the project actually does and what it could potentially do in the future.
- Do not claim that something was tested, implemented, verified, or completed unless this is actually known to be true.

## 8. Code References

- Use exact names for files, classes, functions, methods, variables, APIs, and technologies — copy them verbatim from the source, don't approximate.
- Use inline code formatting (`` `like this` ``) for identifiers, filenames, and short code fragments.
- Use fenced code blocks only when actual code or pseudocode adds clarity beyond what prose can express.
- Do not reproduce large sections of source code in documentation — link or reference the file/location instead, and keep code blocks minimal and illustrative.

## 9. Formatting

Use Markdown structure appropriately:

- Headings and subheadings to organize sections
- Bullet lists for unordered items
- Numbered lists for sequences or ranked items
- Tables when they improve clarity over prose (e.g., comparisons, field references)
- Code blocks only when code/pseudocode is genuinely useful

Unordered lists use `-` as the bullet marker consistently throughout project documentation. Other valid Markdown bullet markers such as `*` are not used as unordered-list markers — this is a documentation formatting convention, not a statement that `*` is invalid Markdown; Markdown emphasis such as `*italic*` and `**bold**` is unaffected.

Avoid excessive nesting (more than 2–3 heading levels deep) and sections that exist only for the sake of completeness. Every section should carry information; delete a section rather than leave it as a placeholder with nothing to say.

## 10. Document Structure

Documentation should be organized as a hierarchy, broken down only as far as the content actually warrants:

Document → Major Section → Subsection → further subdivision (if needed) → details/items

- Major sections separate genuinely distinct topics within the document.
- Subsections break a major section into its component parts, when the section is large or varied enough to need that.
- Further subdivision (a sub-subsection, or simply a labeled paragraph or list) is only justified when it groups a real, distinct sub-topic — not to make the document look more structured than the content is.
- This guide does not prescribe how the hierarchy is labeled or marked — that is a project decision, applied consistently within a document. See §9 for the formatting-level constraint on nesting depth.

Prefer collapsing a level (a bullet list, a bolded lead-in) over adding a heading level for a single, minor point. A hierarchy exists to make content easier to scan and locate — not to formalize every possible subdivision.

When a document has both structural headings and a separate series of individually-referenceable items (rules, requirements, steps) inside its sections, only one of the two should carry numbers as an identity. Number whichever level is the document's actual citation unit; refer to the other level by name, not by a competing number, in cross-references. Two unrelated numbered series sharing the same bare "N." format in one document is what creates ambiguity — not numbering itself.

## 11. Contents

### What a Contents section is

A Contents section is a high-level map of what a document contains — not merely a list of Markdown headings. It lets the reader understand a document's structure, and, for longer technical documents, its important classes, functions, methods, or components, before reading the details.

### Using Contents in practice

- Place `## Contents` near the beginning, after the title and any short intro text. It is not counted among the document's own numbered sections.
- List major sections in their actual order, numbered when it aids navigation.
- Contents normally tracks the major-section level (see §10, Document Structure). Include a subsection only when it is significant enough on its own to be a navigation target — not every subsection, and not individual details or items within a section.
- For larger technical documents, list important classes, functions, methods, or components beneath the section that describes them — only where it genuinely helps navigation.
- Do not force a Contents section onto short or simple documents.
- Keep it synchronized with the actual document.
- Markdown links may be used for navigation, but are a convenience, not the point.

Example:

```markdown
## Contents

1. Overview
2. Object Model
   - `BaseEntity`
   - `SubTypeA`
3. Data Flow
4. Open Questions
```

## 12. Examples

### Architecture description

Weak:
> "The app uses a clean, modern architecture that is easy to extend and maintain."

Better:
> "`OrderService` retrieves data from the REST API and converts the response into `Order` instances. `OrderController` calls `OrderService` and passes the resulting objects to the view layer for rendering."

### Implementation description

Weak:
> "We implemented a robust validation system that handles all edge cases perfectly."

Better:
> "`validateInput()` checks that all required fields are non-empty and that the phone number field contains only digits, with a minimum length of 7. Fields not covered by these two checks are not currently validated."

### Error/limitation description

Weak:
> "There are no known issues with this feature."

Better:
> "Concurrent edits from two browser tabs are not handled — the second save silently overwrites the first. This has not been fixed; tracked as an open limitation."
