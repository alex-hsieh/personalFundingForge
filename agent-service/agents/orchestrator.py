"""
OrchestratorAgent: Coordinates execution of all specialized agents

Purpose: Manage data flow and execution order across all agents
Execution Order: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
"""

from typing import Dict, Any, AsyncGenerator
from .sourcing import run_sourcing_agent
from .matchmaking import run_matchmaking_agent
from .collaborator import run_collaborator_agent
from .drafting import run_drafting_agent


async def orchestrate_pipeline(request: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrates the complete multi-agent pipeline.
    
    Executes agents in sequence: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
    Manages data flow between agents and emits progress updates.
    
    Args:
        request: InvokeRequest dictionary with grantId, grantName, matchCriteria, 
                 eligibility, userProfile, facultyList
                 
    Yields:
        JSON_Line messages with progress updates and final result
    """
    # Extract request fields
    grant_id = request.get("grantId")
    grant_name = request.get("grantName")
    match_criteria = request.get("matchCriteria")
    eligibility = request.get("eligibility")
    user_profile = request.get("userProfile", {})
    faculty_list = request.get("facultyList", [])
    
    # Step 1: SourcingAgent
    yield {
        "agent": "orchestrator",
        "step": "Starting SourcingAgent...",
        "output": None,
        "done": False
    }
    
    sourced_data = {}
    async for json_line in run_sourcing_agent(user_profile):
        yield json_line
        if json_line.get("done"):
            sourced_data = json_line.get("output", {})
    
    # Step 2: MatchmakingAgent
    yield {
        "agent": "orchestrator",
        "step": "Starting MatchmakingAgent...",
        "output": None,
        "done": False
    }
    
    match_result = {}
    async for json_line in run_matchmaking_agent(
        user_profile, sourced_data, match_criteria, eligibility
    ):
        yield json_line
        if json_line.get("done"):
            match_result = json_line.get("output", {})
    
    # Step 3: CollaboratorAgent
    yield {
        "agent": "orchestrator",
        "step": "Starting CollaboratorAgent...",
        "output": None,
        "done": False
    }
    
    collab_result = {}
    async for json_line in run_collaborator_agent(
        faculty_list, match_criteria, user_profile
    ):
        yield json_line
        if json_line.get("done"):
            collab_result = json_line.get("output", {})
    
    # Step 4: DraftingAgent
    yield {
        "agent": "orchestrator",
        "step": "Starting DraftingAgent...",
        "output": None,
        "done": False
    }
    
    draft_result = {}
    async for json_line in run_drafting_agent(
        grant_name,
        match_criteria,
        eligibility,
        match_result.get("matchJustification", ""),
        sourced_data,
        collab_result.get("collaborators", [])
    ):
        yield json_line
        if json_line.get("done"):
            draft_result = json_line.get("output", {})
    
    # Final result aggregation
    result_payload = {
        "proposalDraft": draft_result.get("proposalDraft", ""),
        "collaborators": collab_result.get("collaborators", []),
        "matchScore": match_result.get("matchScore", 0),
        "matchJustification": match_result.get("matchJustification", ""),
        "complianceChecklist": match_result.get("complianceChecklist", [])
    }
    
    # Emit final completion message
    yield {
        "agent": "orchestrator",
        "step": "Complete",
        "output": result_payload,
        "done": True
    }
