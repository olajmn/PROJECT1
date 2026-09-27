"""Canvas pane — visual map face of the bead tree: edit/write, paste.

Node shape and tree-as-text live in project/node/ (above panes).

Files (see docs/04-current-state.md § 2):
  edit_map.py            — + / × / import
  text_to_tree.py        — pasted text → forest of labels
  add_folder/rules.py    — what a folder walk may see (no walk)
  add_folder/walk.py     — applies those rules; one folder → beads (each node keeps its path)
  add_folder/choose.py   — macOS folder dialog → path (no walk)
"""
