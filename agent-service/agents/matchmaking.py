"""
MatchmakingAgent: Analyzes grant fit AND checks policy/compliance

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Dual responsibility - match scoring AND compliance checking
"""

# TODO: Implement MatchmakingAgent
# - Import Agent and BedrockModel from strands packages
# - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
# - Define system prompt for match analysis AND compliance checking (FSU policies, RAMP, COI, IRB)
# - Create matchmaking_agent with Agent(model=fast_model, system_prompt=...)
# - Implement run function that accepts userProfile, sourcedData, matchCriteria, eligibility
# - Return matchScore (0-100), matchJustification, complianceChecklist
# - Yield JSON_Line messages for progress tracking
