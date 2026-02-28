"""
CollaboratorAgent: Finds and ranks relevant faculty collaborators

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Match faculty based on program and expertise keywords
"""

# TODO: Implement CollaboratorAgent
# - Import Agent and BedrockModel from strands packages
# - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
# - Define system prompt for matching faculty based on program and expertise keywords
# - Create collaborator_agent with Agent(model=fast_model, system_prompt=...)
# - Implement run function that accepts facultyList, matchCriteria, userProfile
# - Return top 3 faculty members with name, department, expertise, relevanceScore
# - Yield JSON_Line messages for progress tracking
