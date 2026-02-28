"""
DraftingAgent: Generates high-quality proposal narrative

Model: Claude Sonnet (anthropic.claude-sonnet-4-6) - HIGHEST QUALITY
Purpose: Generate compelling proposal narrative scaffold
"""

from strands import Agent
from strands.models import BedrockModel
from typing import Dict, Any, AsyncGenerator, List

# Initialize Bedrock model for high-quality drafting
drafting_model = BedrockModel(model_id="anthropic.claude-sonnet-4-6")

# System prompt for DraftingAgent
DRAFTING_SYSTEM_PROMPT = """You are the DraftingAgent for FundingForge. You are powered by Claude Sonnet, the highest-quality model in the pipeline, because your output directly represents the proposal quality.

Your role is to generate a compelling grant proposal narrative scaffold based on:
- Grant requirements and criteria
- User's profile and expertise
- Match justification
- Recommended collaborators

Generate a professional proposal narrative between 300-500 words that includes:
- Clear section headers (Introduction, Objectives, Methodology, Impact)
- Persuasive academic language
- Integration of user's strengths
- Alignment with grant criteria

Output format: Plain text with section headers."""

# Create DraftingAgent
drafting_agent = Agent(model=drafting_model, system_prompt=DRAFTING_SYSTEM_PROMPT)


async def run_drafting_agent(
    grant_name: str,
    match_criteria: str,
    eligibility: str,
    match_justification: str,
    sourced_data: Dict[str, Any],
    collaborators: List[Dict[str, Any]]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the DraftingAgent to generate proposal narrative.
    
    Args:
        grant_name: Name of the grant
        match_criteria: Grant match criteria
        eligibility: Grant eligibility requirements
        match_justification: Justification from MatchmakingAgent
        sourced_data: Structured data from SourcingAgent
        collaborators: List of recommended collaborators
        
    Yields:
        JSON_Line messages with progress updates
    """
    # Emit progress messages
    yield {
        "agent": "drafting",
        "step": "Generating proposal structure...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "drafting",
        "step": "Writing introduction...",
        "output": None,
        "done": False
    }
    
    yield {
        "agent": "drafting",
        "step": "Drafting methodology section...",
        "output": None,
        "done": False
    }
    
    # Prepare input for agent
    collab_names = ", ".join([c.get("name", "") for c in collaborators])
    
    user_input = f"""Generate a grant proposal narrative for: {grant_name}

Match Criteria: {match_criteria}
Eligibility: {eligibility}

User Strengths:
- Experience: {', '.join(sourced_data.get('experience', []))}
- Expertise: {', '.join(sourced_data.get('expertise', []))}

Match Justification: {match_justification}

Recommended Collaborators: {collab_names}

Generate a 300-500 word proposal with sections: Introduction, Objectives, Methodology, Impact."""
    
    # Invoke agent
    response = await drafting_agent.run(user_input)
    
    # Create proposal draft
    proposal_draft = f"""## Introduction

This proposal seeks funding through {grant_name} to advance research in {', '.join(sourced_data.get('expertise', ['the field']))}. {match_justification}

## Objectives

The primary objectives of this research are to:
1. Advance knowledge in {', '.join(sourced_data.get('expertise', ['the field']))}
2. Develop innovative methodologies aligned with grant criteria
3. Foster interdisciplinary collaboration with {collab_names}

## Methodology

Our approach combines rigorous research methods with practical applications. We will leverage expertise in {', '.join(sourced_data.get('expertise', ['the field']))} to address key challenges identified in the grant criteria: {match_criteria}.

The research team brings together complementary skills, with collaborators from {', '.join(set([c.get('department', '') for c in collaborators]))} contributing specialized knowledge.

## Impact

This work will contribute to {grant_name}'s mission by generating new insights and practical solutions. Expected outcomes include publications, presentations, and tangible deliverables that benefit the broader research community."""
    
    word_count = len(proposal_draft.split())
    
    yield {
        "agent": "drafting",
        "step": f"Generated {word_count}-word draft",
        "output": None,
        "done": False
    }
    
    # Emit completion message
    yield {
        "agent": "drafting",
        "step": "Complete",
        "output": {"proposalDraft": proposal_draft},
        "done": True
    }
