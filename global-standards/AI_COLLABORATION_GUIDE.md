# AI Collaboration Guide

A reusable standard for how an AI coding session should establish understanding of an existing software project, verify claims against it, and reason and act consistently while working in it. This file is project-independent and can be copied into any software project, alongside `CODE_STYLE_GUIDE.md` and `DOCUMENTATION_STYLE_GUIDE.md`.

## How to use this guide

Provide this file as context to an AI assistant that is about to work in an existing software project — reviewing, extending, or modifying it.

A project may additionally maintain its own collaboration document (for example, a `COLLABORATION.md` at its root) describing how this model applies concretely to that project: which verification tooling it runs, which documents hold its current state, architecture, and decisions, and which specific workflows or tools it uses. Where such a document exists, it takes precedence for anything project-specific — this guide supplies the underlying model, not a project's particular instance of it.

## Scope

This guide governs how an AI session establishes understanding of an existing project, verifies claims against it, reasons about facts, decisions, and open questions, and handles structural change — the collaboration process itself.

It does not govern how source code should be structured (see `CODE_STYLE_GUIDE.md`) or how documentation should be written (see `DOCUMENTATION_STYLE_GUIDE.md`), and it does not define a specific project's own tools, file names, or workflows — those belong in that project's own collaboration document, where one exists.

Code style, documentation style, and a project's own technical conventions are not separate concerns an AI session applies one at a time. Together with a project's current-state, architecture, and decision documentation, they are the specialized material this process works on — this guide describes how that material is read, verified, and acted on; it does not replace what the material itself says.

## Contents

1. Establishing Understanding Before Substantive Work
2. Reading Multiple Sources Together
3. Documentation and Context as Orientation, Not Proof
4. Verifying Against Actual Code, Structure, or Runtime
5. Distinguishing Fact, Hypothesis, Decision, and Open Question
6. Respecting Existing Decisions and Project Continuity
7. Avoiding Assumptions About Structure and Paths
8. Handling Structural Changes
9. Keeping Current State Consistent With Documentation
10. Scaling Verification Effort to Stakes

## 1. Establishing Understanding Before Substantive Work

Before making changes or claims that matter, establish what is actually true about the project right now, rather than reconstructing its shape from memory, training data, or general conventions. Where the project provides automated verification or health-check tooling, run it; where it maintains a document describing its current state, read it.

Treat tooling output as what is mechanically observable right now, and a narrative status document as believed context, not verified fact, until confirmed. A clean or passing check means the checks it runs found nothing wrong — not that the project as a whole is verified; it only covers what it actually checks.

## 2. Reading Multiple Sources Together

A project's documentation can serve several distinct purposes, each carrying a different kind of reliability. Before treating a document as an answer, identify what kind of question it is actually suited to answer:

- State ("what is true now") — a current-state or status document: orientation, not proof.
- Intent ("how it's meant to work or be structured") — an architecture or design document: describes intent, not what has actually been built.
- Rationale ("why was it done this way") — a decisions or rationale record: settled, unless explicitly flagged as reopened.
- History ("what happened, and when") — a changelog or development log: accurate for the date it was written, not for today.
- Speculation ("what might happen") — a backlog, parking lot, or ideas list: not decided, not built.

Map these roles onto whichever documents the project actually maintains, and read them against each other rather than trusting any single one in isolation. Agreement between sources strengthens a claim only if those sources were actually produced independently of each other — a document that merely restates or copies another is not a second source. When sources disagree, don't average or guess: flag the conflict explicitly, and verify against the underlying reality directly rather than picking a side.

## 3. Documentation and Context as Orientation, Not Proof

Documentation, prior context, and a session's own earlier statements — including from earlier in the same conversation — are orientation, not proof. They describe what was believed or true at some point, not necessarily what is true now. When a concrete claim about current code, structure, or runtime behavior matters for a decision or a change, verify the relevant reality before building on it, rather than treating an existing description as settled, however recent, detailed, or previously confirmed it is.

A historical or dated entry compounds this: it is accurate for the date it was written, not for today. Repeating it as present-tense fact is a misuse of the record, not the record failing.

## 4. Verifying Against Actual Code, Structure, or Runtime

Verify a claim the cheap way before acting on it — list a directory, search the code, read the file, or run the thing — rather than reasoning from what should logically be there. This applies in particular to:

- A specific file path or project structure, right before it is acted on.
- A claim taken from documentation that is about to drive a decision or a change.
- A claim carried over from earlier in the same session, once meaningful time or changes have passed since it was last checked.

Confidence, or having stated something already, is not evidence.

## 5. Distinguishing Fact, Hypothesis, Decision, and Open Question

Keep four things separate, in what is read and what is written: a fact (true now), a hypothesis (an untested belief), a decision (settled, with a reason), and an open question (not yet resolved). Don't present a hypothesis as a fact, and don't treat a settled decision as reopened without saying so explicitly.

Where a project's documentation standard already defines a related taxonomy for written output (see `DOCUMENTATION_STYLE_GUIDE.md` §5), treat this as that same underlying distinction — separating what's confirmed from what's believed, decided, or still open — applied to how an AI session reasons and acts during a task, not as a competing one.

## 6. Respecting Existing Decisions and Project Continuity

A settled, recorded decision is not revisited casually. If one appears wrong given new information, say why and flag it explicitly, rather than quietly working around it or reintroducing the alternative it ruled out.

Equally, a well-reasoned idea sitting in a backlog, or anything explicitly marked open or undecided, is not a decision no matter how thorough it reads — state it as parked or open when referring to it, not as settled.

## 7. Avoiding Assumptions About Structure and Paths

Do not state a file path, directory structure, or project fact from memory when it is about to be acted on or asserted as true. This holds regardless of how confident the assumption feels or how recently the structure was last checked — check first, every time.

## 8. Handling Structural Changes

Before renaming, moving, or deleting anything another file, document, or piece of code might reference, search the whole project — documentation and code — for references to the old name or location first. Every reference found gets updated, or is deliberately left with a stated reason; none are silently skipped.

Where the project has automated consistency checks, run them afterward as a backstop for what the search might have missed — not as a substitute for doing the search.

## 9. Keeping Current State Consistent With Documentation

If the work done in a session changes what is true about the project, update whatever documentation the project treats as its source of current-state truth before ending the session, if such a document exists. A stale current-state document can be worse than none: it continues to be trusted by default, while a missing one at least signals its own absence.

## 10. Scaling Verification Effort to Stakes

Verification effort should scale with what is riding on the claim. Casual orientation does not need the rigor that a claim driving an edit, a structural change, or something written into documentation as fact does. Where a project offers cheap, automated verification, it is generally worth re-running before a consequential claim or change.