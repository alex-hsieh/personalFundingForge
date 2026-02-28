"""
FundingForge Agent Service - Specialized Agents Package

This package contains all specialized agents for the multi-agent pipeline:
- SourcingAgent: Extracts and structures user CV and profile data
- MatchmakingAgent: Analyzes grant fit and checks policy/compliance
- CollaboratorAgent: Finds and ranks relevant faculty collaborators
- DraftingAgent: Generates high-quality proposal narrative
- OrchestratorAgent: Coordinates execution of all specialized agents
"""

from .sourcing import run_sourcing_agent
from .matchmaking import run_matchmaking_agent
from .collaborator import run_collaborator_agent
from .drafting import run_drafting_agent
from .orchestrator import orchestrate_pipeline

__all__ = [
    "run_sourcing_agent",
    "run_matchmaking_agent",
    "run_collaborator_agent",
    "run_drafting_agent",
    "orchestrate_pipeline"
]
