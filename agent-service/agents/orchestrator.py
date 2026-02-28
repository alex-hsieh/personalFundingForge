"""
OrchestratorAgent: Coordinates execution of all specialized agents

Purpose: Manage data flow and execution order across all agents
Execution Order: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
"""

# TODO: Implement OrchestratorAgent
# - Import all specialized agents (sourcing, matchmaking, collaborator, drafting)
# - Define orchestrate_pipeline async function that accepts InvokeRequest
# - Implement sequential execution: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
# - Pass outputs from each agent to subsequent agents as needed
# - Yield progress JSON_Line messages after each agent completes
# - After all agents complete, construct Result_Payload with proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
# - Yield final JSON_Line with agent="orchestrator", step="Complete", output=Result_Payload, done=True
# - Ensure no markdown fencing in JSON responses
