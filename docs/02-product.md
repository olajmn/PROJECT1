# 02 — Product

What the product is today: the foundation it rests on, and the app on
top of it.

## 1. The foundation

What the product delivers underneath any screen: a node model that holds
up on its own ([[00-project-brief]] § 2).

- **Nodes as objects:** each node has a stable identity and its own
  state; its name does not identify it ([[05-decisions]] #52).
- **Parent–child structure** at any depth, with children in order.
- **Reusable structures:** a branch can be saved and placed elsewhere as
  a new instance with new identities ([[05-decisions]] #54).
- **Readable by a system:** the nodes and their relations are data an AI
  can be given directly, whole or one node at a time.

### i. Principles

- **Code owns state and identity; the model only assists.** Storage,
  ids, and structure are deterministic; the model is used for
  conversation and suggestions.
- **A clean, self-contained data model**, so it can be built on.

### ii. Success

The model holds up in real use: identities stay stable, relations stay
clean, and structures can be moved and reused without breaking.

## 2. The app

The app is where the foundation is used and tested.

### i. What it is

A local web app with **accounts**, **projects**, a **map** of nodes for
each project, and a **conversation** beside it, laid out as three
columns. The user builds and reorganizes the nodes; the conversation
helps but does not take over.

| Column | What it holds |
|---|---|
| **Sidebar** | Accounts, each with its projects; `+` for a new project; Settings (General, Directory, Archive, Logs) |
| **Canvas** | The open project's map: nodes under the project title, each with a ⋯ menu; depth (− / +) and Text / Line view on top; Copy as ASCII, Paste structure, Add folder, Saved trees, and Archive below |
| **Chat** | Current state of the project, the conversation thread (turns about a node are framed and can be shown on their own), and the message box with a `/` command menu |

### ii. What you can do

- **Projects and accounts:** switch account in the sidebar. Create a
  project with `+` — give it a name, leave it empty for `New project N`,
  or start it from a folder on disk. Rename a project by clicking its
  title on the map; archive it from the bar under the map. Projects
  without an account can be assigned to the active one from the
  Accounts panel.
- **Build the map:** add a node (`+` at the end, or ⋯ Add here) and
  remove one (⋯ Remove). Paste an outline — bullets, a numbered list,
  plain lines, or an ASCII tree — with a live preview where single nodes
  can be left out. Add a folder from disk: each file and folder becomes
  a node. Ask for suggested children (⋯ Suggest structure). A name that
  already exists among siblings gets `(2)`, `(3)`, … instead of an
  error.
- **Reuse structure:** save a node and everything under it (⋯ Save as
  tree), then insert it again from ⋯ Insert saved tree… (under that
  node) or **Saved trees** in the bar under the map (under the selected
  node, or at the top level). Each insert gets new nodes of its own; ×
  in the list deletes a saved tree from the library only.
- **Read the map:** show fewer or more levels (− / +), switch between
  Text and Line view, zoom with the scroll wheel, pan by dragging,
  double-click to reset the view, and jump to the top (↑). Copy as
  ASCII copies the whole structure as text.
- **Talk:** chat about the whole project, or select a node (click it, or
  ⋯ Talk about this) to talk about that node. Turns about a node are
  framed in the thread, and "Show only this" shows them on their own.
  With a node selected, asking for structure adds suggested children,
  and a message of several lines is added as nodes under it.
- **Current state:** the panel above the chat shows the project, its
  last change, the size of the map, and changes per day; node names in
  it select that node on the map. The conversation is given the same
  summary.
- **Commands:** type `/` or use the `/` button next to Send.
  `/project_summary` summarises the structure; `/add Name` or
  `/add Parent / Child` adds a node; `/select Parent / Child` selects
  one; `/id` shows the selected node's id, or switches the whole map
  between ids and names. An unknown command gets a fixed reply.
- **Look back:** Settings → Logs lists every saved change, across all
  projects or as one project's full timeline. Settings → Archive holds
  archived accounts and projects, to restore or delete for good.
- **Settings:** General sets light or dark appearance and shows which
  model is used; Directory creates, renames, and archives accounts.

### iii. Not in the app (for now)

- Real accounts, login, multi-user, sync, or a mobile app

### iv. Success

A session succeeds when the user's structure is clearer than when they
started — not when the conversation has produced something complete on
its own.

## See also

- [[00-project-brief]]
- [[surfaces]] — sidebar / canvas / chat roles
- [[04-current-state]]
- [[03-architecture]]
- [[05-decisions]]
