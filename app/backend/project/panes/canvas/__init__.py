"""Canvas pane — WHAT bead tree: shape, edit/write, paste, suggest.

Files (see docs/04-current-state.md § 2.iv):
  bead.py                — one map bead (Step shape)
  read_map/outline.py    — map as indented labels (no call)
  read_map/read.py       — sends Read map brief (model/brief/read_map); tree → summary, no write
  edit_map.py            — + / × / import / Suggest / chat-suggest
  text_to_tree.py        — pasted text → forest of labels
  add_folder/rules.py    — what a folder walk may see (no walk)
  add_folder/walk.py     — applies those rules; one folder → beads (each node keeps its path)
  add_folder/choose.py   — macOS folder dialog → path (no walk)
  call_suggest.py        — Suggest call + parse; prompts in model/brief/suggest (no write)
"""
