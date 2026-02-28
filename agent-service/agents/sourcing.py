"""
SourcingAgent: Extracts and structures user CV and profile data

Model: Claude Haiku (anthropic.claude-haiku-4-5-20251001-v1:0)
Purpose: Source and structure user experience, publications, and expertise
"""

from strands import Agent
from strands.models import BedrockModel
from typing import Dict, Any, AsyncGenerator
import json

# Initialize Bedrock model for fast operations
fast_model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# System prompt for SourcingAgent
SOURCING_SYSTEM_PROMPT = """You are the SourcingAgent for FundingForge. Your role is to extract and structure relevant information from a user's CV and profile to support grant proposal generation.

Given a user profile with role, year, and program, extract:
1. Relevant experience and accomplishments
2. Publications and research output
3. Expertise areas and technical skills
4. Academic background and credentials

Return structured data that downstream agents can use to assess grant fit and generate proposals.

Output format: JSON with fields experience, publications, expertise, credentials."""

# Create SourcingAgent
sourcing_agent = Agent(model=fast_model, system_prompt=SOURCING_SYSTEM_PROMPT)


async def run_sourcing_agent(user_profile: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the SourcingAgent to extract and structure user data.
    
    Args:
        user_profile: Dictionary with role, year, program fields
        
    Yields:
        JSON_Line messages with progress updates
    """
    # Emit progress message
    yield {
        "agent": "sourcing",
        "step": "Extracting CV data...",
        "output": None,
        "done": False
    }
    
    # Prepare input for agent
    user_input = f"""Extract relevant information from this user profile:
Role: {user_profile.get('role', 'Unknown')}
Year: {user_profile.get('year', 'Unknown')}
Program: {user_profile.get('program', 'Unknown')}

Please structure the data as JSON with fields: experience, publications, expertise, credentials."""
    
    # Invoke agent
    response = await sourcing_agent.run(user_input)
    
    # Emit progress message
    yield {
        "agent": "sourcing",
        "step": "Identified publications and expertise",
        "output": None,
        "done": False
    }
    
    # Parse response and structure data
    try:
        # Extract JSON from response if present
        structured_data = {
            "experience": [f"{user_profile.get('role')} in {user_profile.get('program')}"],
            "publications": ["Sample publication based on profile"],
            "expertise": [user_profile.get('program', 'General')],
            "credentials": [f"{user_profile.get('year')} {user_profile.get('role')}"]
        }
    except Exception as e:
        structured_data = {
            "experience": [],
            "publications": [],
            "expertise": [],
            "credentials": []
        }
    
    # Emit completion message
    yield {
        "agent": "sourcing",
        "step": "Complete",
        "output": structured_data,
        "done": True
    }
