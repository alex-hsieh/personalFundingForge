"""
DraftingAgent: Generates high-quality proposal narrative

Model: Claude Sonnet (anthropic.claude-sonnet-4-6) - HIGHEST QUALITY
Purpose: Generate compelling proposal narrative scaffold
"""

# TODO: Implement DraftingAgent
# - Import Agent and BedrockModel from strands packages
# - Instantiate drafting_model with BedrockModel(model_id="anthropic.claude-sonnet-4-6")
# - Define system prompt for generating high-quality proposal narrative with section headers
# - Create drafting_agent with Agent(model=drafting_model, system_prompt=...)
# - Implement run function that accepts grantName, matchCriteria, eligibility, matchJustification, sourcedData, collaborators
# - Return proposalDraft (300-500 words with section headers)
# - Yield JSON_Line messages for progress tracking
