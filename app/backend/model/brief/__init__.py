"""Pack project data + prompts into what the external model is told.

No model call, nothing saved. Call sites (chat reply, canvas Suggest,
/project_summary) import from here and send via model.client.
"""
