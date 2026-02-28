"""
SourcingAgent: Extracts and structures user CV and profile data

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Source and structure user experience, publications, and expertise
"""

# TODO: Implement SourcingAgent
# - Import Agent and BedrockModel from strands packages
# - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
# - Define system prompt for extracting user experience, publications, expertise, credentials
# - Create sourcing_agent with Agent(model=fast_model, system_prompt=...)
# - Implement run function that accepts userProfile and returns structured data
# - Yield JSON_Line messages for progress tracking
