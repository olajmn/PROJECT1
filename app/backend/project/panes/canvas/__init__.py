"""Canvas pane — WHAT bead tree: shape, first mint, edit/write, paste, suggest.

Files (see docs/04-current-state.md § 2.iv):
  bead.py                — one map bead (Step shape)
  call_read.py           — LLM call that reads a tree back into a
                           summary (no write)
  construct_first_map.py — coarse middle mint (on request; not auto on PLAN)
  edit_map.py            — + / × / import / Suggest / chat-suggest
  text_to_tree.py        — pasted text → forest of labels
  add_folder/walk.py     — one folder on disk → tree of beads (each node keeps its path)
  add_folder/choose.py   — macOS folder dialog → path (no walk)
  call_suggest.py        — LLM call that proposes children (no write)
"""
