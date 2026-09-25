"""Read map — the instruction sent to the model.

Not chat. Read map is given the labels already on the
map and asked what that structure appears to be. It does not read file
contents. The string below is the whole instruction. `read.py` sends it.
"""

READ_MAP_SYSTEM_PROMPT = (
    "You are given the structure of a project someone has already "
    "built or pasted in - a tree of labels, indented to show what "
    "sits under what. Nobody has written down what the project is "
    "about; that is what you work out from the structure alone.\n\n"
    "Return `summary`: a few sentences on what this project appears "
    "to be about - what it covers, how it is organised, and what "
    "kind of work it implies. Describe what is actually there. Do "
    "not recommend, judge whether it is good, or propose what is "
    "missing."
)
