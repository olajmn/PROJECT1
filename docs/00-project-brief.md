# 00 — Project Brief

What this project is, in short.

## 1. What it is

**PROJECT1** is a workspace for building things out of **nodes**. At its core, the
project is about the node itself: what a node is, what makes it the
same node over time, and how nodes relate to each other. In use, you
build, sort, and restructure nodes.

## 2. Core ideas

- **The node is the building block.** A node is an object. It has a
  stable identity of its own and carries its own information and
  state. Its label is only text; it does not identify the node
  ([[05-decisions]] #52).
- **Structures are self-contained.** Each node has one parent and any
  number of children. That relation gives whatever the nodes describe
  its shape, at whatever depth it needs. A branch can be lifted out,
  kept, and placed elsewhere as a new instance within the structure
  with its own identity ([[05-decisions]] #54).
- **The conversation.** The structure creates context through its
  shape and history, and gives the AI a natural data set to work with.
  It can read the system as a whole, and focus on specific nodes by
  selection.

## 3. What it is not

- Not a planner or a to-do app: there is no schedule or task engine.
- Not an agent that decides for the user.
- Not tied to one kind of content: a recipe, a building design, or a
  folder on disk is the same kind of structure.
