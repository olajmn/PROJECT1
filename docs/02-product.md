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
  conversation only and never writes to the project.
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
| **Canvas** | The open project's map: nodes under the project title, each with a ⋯ menu; depth (− / +) and Text / Line view on top; below it **+ Add** (Paste structure, Add folder, Insert saved tree…) and icon buttons for Copy as ASCII and Archive |
| **Chat** | Current state of the project, the conversation thread (turns about a node are framed and can be shown on their own), and the message box with a `/` command menu |

### ii. What you can do

- **Projects and accounts:** switch account in the sidebar. Create a
  project with `+` — give it a name, leave it empty for `New project N`,
  or start it from a folder on disk. Rename a project by clicking its
  title on the map; archive it from the bar under the map. Projects
  without an account can be assigned to the active one from the
  Accounts panel.
- **Build the map:** add a node (`+` at the end, or ⋯ Add here) and
  remove one (⋯ Remove; a node with children asks first, since its
  children go with it). Move a node up or down among its siblings
  (⋯ Move up / Move down; everything under it moves along). Paste an outline — bullets, a numbered list,
  plain lines, or an ASCII tree — with a live preview where single nodes
  can be left out. Add a folder from disk: each file and folder becomes
  a node. A name that already exists among siblings gets `(2)`,
  `(3)`, … instead of an error.
- **Reuse structure:** save a node and everything under it (⋯ Save as
  tree), then insert it again from ⋯ Insert saved tree… (under that
  node) or **+ Add → Insert saved tree…** in the bar under the map (under the selected
  node, or at the top level). Each insert gets new nodes of its own; ×
  in the list deletes a saved tree from the library only.
- **Read the map:** show fewer or more levels (− / +), switch between
  Text and Line view, pan by scrolling or dragging, zoom by pinching
  or Ctrl/Cmd+scroll,
  double-click to reset the view, and jump to the top (↑). Copy as
  ASCII copies the whole structure as text.
- **Talk:** chat about the whole project, or select a node (click it, or
  ⋯ Talk about this) to talk about that node. Turns about a node are
  framed in the thread, and "Show only this" shows them on their own.
  With a node selected, a message of several lines is added as nodes
  under it.
- **Current state:** the panel above the chat shows the project, when
  it was created, its last change, the size of the map, and changes per
  day (creating the project is not counted as a change); node names in
  it select that node on the map, and a day with changes selects that
  day for the conversation. The conversation is given the same
  summary rows and the changes themselves.
- **Commands:** type `/` or use the `/` button next to Send.
  `/add Name` or `/add Parent / Child` adds a node;
  `/select Parent / Child` selects one; `/id` shows the selected node's id, or switches the whole map
  between ids and names. An unknown command gets a fixed reply.
- **Look back:** Settings → Logs lists every saved change by day,
  across all projects (the newest 200, then Show more) or as one
  project's full timeline. Settings → Archive holds
  archived accounts and projects, to restore or delete for good.
- **Settings:** General sets light or dark appearance and shows which
  model is used; Directory creates, renames, and archives accounts.

### iii. What Talk should handle

The minimum the conversation must get right. Talk answers from the
project only: it does not invent details, change the project, or offer
to (`backend/model/brief/talk_prompt.py`).

1. **A greeting or small talk** ("hi", "cool!", "thanks") gets a short
   reply: no question back, no summary of the project.
2. **"What is this project about?"** gets one or two sentences that
   name its parts.
3. **With a node selected, "what should I do here?"** gets the parts
   under that node, without assuming any of them are done.
4. **A question the project cannot answer** ("how long does this
   take?", "what have I finished?") gets a plain "the project doesn't
   say", not a guess.
5. **"What changed today?"**, or a day selected in Current state, gets
   the actual changes, not the chat.
6. **"Can you add …?"** gets a plain no: the user adds parts.

If the model is not running, Send shows "the model is not running -
start Ollama and try again" and nothing is saved.

### iv. Not in the app (for now)

- Real accounts, login, multi-user, sync, or a mobile app

### v. Success

A session succeeds when the user's structure is clearer than when they
started — not when the conversation has produced something complete on
its own.

## See also

- [[00-project-brief]]
- [[ui]] — the screen: columns, canvas layout, look
- [[04-current-state]]
- [[03-architecture]]
- [[05-decisions]]
