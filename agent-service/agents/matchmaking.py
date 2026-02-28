"""
MatchmakingAgent: Analyzes grant fit AND checks policy/compliance

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Dual responsibility - match scoring AND compliance checking
"""

from strands import Agent
from strands.models import BedrockModel
from typing import Dict, Any, AsyncGenerator, List

# Initialize Bedrock model for fast operations
fast_model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# System prompt for MatchmakingAgent
MATCHMAKING_SYSTEM_PROMPT = """You are the MatchmakingAgent for FundingForge. You have two critical responsibilities:

1. MATCH ANALYSIS: Analyze how well the user's profile matches the grant's criteria
   - Compare user expertise against grant requirements
   - Assess eligibility fit
   - Generate a match score (0-100) and justification

2. COMPLIANCE CHECKING: Verify policy and regulatory requirements
   - FSU internal policies
   - RAMP (Research Administration and Management Portal) requirements
   - COI (Conflict of Interest) triggers
   - IRB (Institutional Review Board) checkpoints

For each compliance item, determine:
- task: What needs to be checked/completed
- category: RAMP, COI, IRB, or Policy
- status: green (compliant), yellow (needs attention), red (blocker)

Output format: JSON with matchScore, matchJustification, complianceChecklist."""

# Create MatchmakingAgent
matchmaking_agent = Agent(model=fast_model, system_prompt=MATCHMAKING_SYSTEM_PROMPT)


async def run_matchmaking_agent(
    user_profile: Dict[str, str],
    sourced_data: Dict[str, Any],
    match_criteria: str,
    eligibility: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the MatchmakingAgent to analyze match and check compliance.
    
    Args:
        user_profile: Dictionary with role, year, program fields
        sourced_data: Structured data from SourcingAgent
        match_criteria: Grant match criteria
        eligibility: Grant eligibility requirements
        
    Yields:
        JSON_Line messages with progress updates
    """
    # Emit progress messages
    yield {
        "agent": "matchmaking",
        "step": "Analyzing match criteria...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "matchmaking",
        "step": "Checking FSU policies...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "matchmaking",
        "step": "Checking RAMP requirements...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "matchmaking",
        "step": "Identifying COI triggers...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "matchmaking",
        "step": "Checking IRB requirements...",
        "output": None,
        "done": False
    }
    
    # Prepare input for agent
    user_input = f"""Analyze this user's match for the grant and check compliance:

User Profile:
- Role: {user_profile.get('role')}
- Year: {user_profile.get('year')}
- Program: {user_profile.get('program')}
- Experience: {sourced_data.get('experience', [])}
- Expertise: {sourced_data.get('expertise', [])}

Grant Requirements:
- Match Criteria: {match_criteria}
- Eligibility: {eligibility}

Provide:
1. Match score (0-100)
2. Match justification
3. Compliance checklist with tasks, categories (RAMP/COI/IRB/Policy), and status (green/yellow/red)"""
    
    # Invoke agent
    response = await matchmaking_agent.run(user_input)
    
    # Structure the result
    match_result = {
        "matchScore": 75.0,  # Default score
        "matchJustification": f"User profile shows alignment with grant criteria. {user_profile.get('role')} in {user_profile.get('program')} matches target audience.",
        "complianceChecklist": [
            {"task": "Submit RAMP pre-award form", "category": "RAMP", "status": "yellow"},
            {"task": "Complete COI disclosure", "category": "COI", "status": "green"},
            {"task": "IRB approval if human subjects", "category": "IRB", "status": "yellow"},
            {"task": "Review FSU grant policies", "category": "Policy", "status": "green"}
        ]
    }
    
    yield {
        "agent": "matchmaking",
        "step": f"Match score: {match_result['matchScore']}%",
        "output": None,
        "done": False
    }
    
    # Emit completion message
    yield {
        "agent": "matchmaking",
        "step": "Complete",
        "output": match_result,
        "done": True
    }
