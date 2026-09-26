"""Project summary — instruction + schema sent to the model.

Given node labels (tree as text), ask what the project appears to
be about. Does not read file contents. Talk `/project_summary` runs this.
"""

PROJECT_SUMMARY_SYSTEM_PROMPT = (
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

PROJECT_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
    },
    "required": ["summary"],
}
