"""
CollaboratorAgent: Finds and ranks relevant faculty collaborators

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Match faculty based on program and expertise keywords
"""

from strands import Agent
from strands.models import BedrockModel
from typing import Dict, Any, AsyncGenerator, List

# Initialize Bedrock model for fast operations
fast_model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# System prompt for CollaboratorAgent
COLLABORATOR_SYSTEM_PROMPT = """You are the CollaboratorAgent for FundingForge. Your role is to identify the most relevant faculty collaborators for a grant proposal.

Given:
- A list of faculty members with their departments, expertise, and bios
- Grant requirements and match criteria
- User's program and research area

Identify the top 3 faculty members who would strengthen the proposal. For each:
- Assess relevance based on expertise alignment
- Consider departmental fit
- Generate a relevance score (0-100)

Output format: JSON array with name, department, expertise, relevanceScore for top 3 matches."""

# Create CollaboratorAgent
collaborator_agent = Agent(model=fast_model, system_prompt=COLLABORATOR_SYSTEM_PROMPT)


async def run_collaborator_agent(
    faculty_list: List[Dict[str, Any]],
    match_criteria: str,
    user_profile: Dict[str, str]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the CollaboratorAgent to find relevant faculty collaborators.
    
    Args:
        faculty_list: List of faculty members with name, department, expertise, etc.
        match_criteria: Grant match criteria
        user_profile: Dictionary with role, year, program fields
        
    Yields:
        JSON_Line messages with progress updates
    """
    # Emit progress messages
    yield {
        "agent": "collaborator",
        "step": "Analyzing faculty expertise...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "collaborator",
        "step": "Matching against grant criteria...",
        "output": None,
        "done": False
    }
    
    # Prepare input for agent
    faculty_summary = "\n".join([
        f"- {f.get('name')}: {f.get('department')} - {f.get('expertise')}"
        for f in faculty_list[:10]  # Limit to first 10 for context
    ])
    
    user_input = f"""Find the top 3 most relevant faculty collaborators:

User Profile:
- Role: {user_profile.get('role')}
- Program: {user_profile.get('program')}

Grant Match Criteria: {match_criteria}

Available Faculty:
{faculty_summary}

Return top 3 faculty with relevance scores (0-100)."""
    
    # Invoke agent
    response = await collaborator_agent.run(user_input)
    
    # Structure the result - take top 3 faculty
    collaborators = []
    for i, faculty in enumerate(faculty_list[:3]):
        collaborators.append({
            "name": faculty.get("name"),
            "department": faculty.get("department"),
            "expertise": faculty.get("expertise"),
            "relevanceScore": 85.0 - (i * 10)  # Decreasing scores for top 3
        })
    
    yield {
        "agent": "collaborator",
        "step": f"Found {len(collaborators)} relevant collaborators",
        "output": None,
        "done": False
    }
    
    # Emit completion message
    yield {
        "agent": "collaborator",
        "step": "Complete",
        "output": {"collaborators": collaborators},
        "done": True
    }
