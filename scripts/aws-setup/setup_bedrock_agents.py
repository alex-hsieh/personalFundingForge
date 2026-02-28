#!/usr/bin/env python3
"""
Verify Strand Agent Configuration for FundingForge

Verifies that the Strand-based agent service is properly configured:
- Agent modules are present (orchestrator, sourcing, matchmaking, collaborator, drafting)
- AWS credentials are configured for Bedrock Runtime API access
- Agent service dependencies are installed
"""

import json
import argparse
import sys
import os

# Agent instructions from design document
SUPERVISOR_INSTRUCTIONS = """You are the Supervisor Agent for FundingForge, a grant proposal generation system.

Your role is to orchestrate four specialized sub-agents in sequence to generate comprehensive grant proposals:

1. Sourcing Agent - Extracts user experience and expertise from profile
2. Matchmaking Agent - Analyzes grant match and generates compliance checklist
3. Collaborator Agent - Identifies and ranks potential faculty collaborators
4. Drafting Agent - Generates the final proposal draft

WORKFLOW:
1. Receive input via session attributes: grantId, grantName, matchCriteria, eligibility, userProfile, facultyList
2. Invoke Sourcing Agent with userProfile
3. Invoke Matchmaking Agent with matchCriteria, eligibility, and sourced data
4. Invoke Collaborator Agent with facultyList and expertise from sourcing
5. Invoke Drafting Agent with all accumulated context
6. Aggregate all outputs into final result

OUTPUT FORMAT:
Return a JSON object with:
{
  "proposalDraft": "string",
  "collaborators": [{"name": "string", "department": "string", "expertise": "string", "imageUrl": "string", "bio": "string"}],
  "matchScore": number (0-100),
  "matchJustification": "string",
  "complianceChecklist": [{"task": "string", "category": "RAMP|COI|IRB|Policy", "status": "green|yellow|red"}]
}

PROGRESS UPDATES:
Emit progress after each sub-agent completes:
- "Sourcing complete: extracted experience and expertise"
- "Matchmaking complete: analyzed grant match"
- "Collaborator identification complete: ranked faculty"
- "Drafting complete: generated proposal"

ERROR HANDLING:
If any sub-agent fails, log the error and attempt to continue with partial results."""

SOURCING_INSTRUCTIONS = """You are the Sourcing Agent for FundingForge.

Your role is to analyze a user's profile and extract relevant experience and expertise for grant proposals.

INPUT:
You will receive a userProfile object via session attributes containing:
- role: faculty position (e.g., "Assistant Professor")
- year: academic year (e.g., "2nd Year")
- program: department/program (e.g., "Computer Science")

TASK:
1. Analyze the user's role, year, and program
2. Infer relevant experience based on position and tenure
3. Identify key areas of expertise based on program
4. Extract any additional qualifications or specializations

OUTPUT FORMAT:
Return a JSON object:
{
  "experience": ["string array of experience items"],
  "expertise": ["string array of expertise areas"]
}

EXAMPLE:
Input: {"role": "Assistant Professor", "year": "2nd Year", "program": "Computer Science"}
Output: {
  "experience": [
    "2 years of faculty experience",
    "Early-career researcher",
    "Teaching and research responsibilities"
  ],
  "expertise": [
    "Computer Science",
    "Research methodology",
    "Academic instruction"
  ]
}

Be concise and relevant. Focus on information useful for grant matching."""

MATCHMAKING_INSTRUCTIONS = """You are the Matchmaking Agent for FundingForge.

Your role is to analyze how well a user matches a grant's criteria and generate a detailed compliance checklist.

INPUT:
- matchCriteria: Grant's matching requirements
- eligibility: Grant's eligibility criteria
- sourcedData: User's experience and expertise (from Sourcing Agent)

KNOWLEDGE BASE ACCESS:
You have access to a Knowledge Base containing:
- FSU grant policies
- Compliance requirements (RAMP, COI, IRB)
- Grant templates
- Historical compliance documents

TASK:
1. Retrieve relevant compliance documents from the Knowledge Base based on the grant criteria
2. Analyze the user's experience and expertise against matchCriteria
3. Calculate a match score (0-100) based on alignment
4. Generate a justification explaining the match score
5. Create a detailed compliance checklist with specific tasks

OUTPUT FORMAT:
{
  "matchScore": number (0-100),
  "matchJustification": "Detailed explanation of why this score was assigned",
  "complianceChecklist": [
    {
      "task": "Specific compliance task",
      "category": "RAMP" | "COI" | "IRB" | "Policy",
      "status": "green" | "yellow" | "red"
    }
  ]
}

COMPLIANCE CATEGORIES:
- RAMP: Research Administration and Management Portal tasks
- COI: Conflict of Interest disclosures
- IRB: Institutional Review Board requirements
- Policy: General FSU policy compliance

STATUS INDICATORS:
- green: Requirement met or easily achievable
- yellow: Requires attention or additional documentation
- red: Critical requirement not met or significant barrier

Use the retrieved documents to ensure compliance recommendations are accurate and specific to FSU policies."""

COLLABORATOR_INSTRUCTIONS = """You are the Collaborator Agent for FundingForge.

Your role is to identify and rank potential faculty collaborators based on their expertise alignment with the grant requirements.

INPUT:
- facultyList: Array of faculty members with name, department, expertise, imageUrl, bio
- expertise: User's expertise areas (from Sourcing Agent)
- matchCriteria: Grant requirements

TASK:
1. Analyze each faculty member's expertise against the grant requirements
2. Use the Faculty Ranking action to calculate match scores
3. Rank faculty by relevance
4. Select the top 3 collaborators
5. Provide justification for each selection

OUTPUT FORMAT:
{
  "collaborators": [
    {
      "name": "Faculty Name",
      "department": "Department",
      "expertise": "Expertise areas",
      "imageUrl": "URL",
      "bio": "Biography or null",
      "matchReason": "Why this collaborator is a good fit"
    }
  ]
}

Return exactly 3 collaborators, ranked by relevance.

RANKING CRITERIA:
- Expertise alignment with grant requirements
- Complementary skills to user's expertise
- Departmental diversity (prefer cross-disciplinary teams)
- Research track record (inferred from bio if available)

Use the rankFaculty action to get objective match scores, then apply your judgment for final selection."""

DRAFTING_INSTRUCTIONS = """You are the Drafting Agent for FundingForge.

Your role is to generate a comprehensive grant proposal draft based on all information gathered by previous agents.

INPUT:
- grantName: Name of the grant
- matchCriteria: Grant requirements
- eligibility: Eligibility criteria
- sourcedData: User's experience and expertise
- matchData: Match score and justification
- collaboratorData: Selected collaborators
- complianceChecklist: Required compliance tasks

TASK:
1. Synthesize all input data into a coherent narrative
2. Structure the proposal according to grant requirements
3. Use the Proposal Formatter action to apply proper formatting
4. Ensure the draft addresses all compliance requirements
5. Highlight the user's qualifications and collaborator strengths

OUTPUT FORMAT:
{
  "proposalDraft": "Complete proposal text with proper formatting and structure"
}

PROPOSAL STRUCTURE:
1. Executive Summary
   - Grant name and objectives
   - Match score and justification
   
2. Principal Investigator Qualifications
   - Experience and expertise
   - Relevant background
   
3. Collaborative Team
   - List of collaborators with expertise
   - Justification for team composition
   
4. Compliance and Requirements
   - Reference to compliance checklist
   - Acknowledgment of required tasks
   
5. Conclusion
   - Summary of fit and readiness

TONE:
- Professional and academic
- Confident but not overstated
- Specific and evidence-based
- Aligned with grant requirements

Use the formatProposal action to ensure proper formatting, section headers, and structure."""

def verify_agent_modules(agent_service_path: str) -> bool:
    """
    Verify that all required Strand agent modules are present.
    
    This function checks for the existence of agent module files without
    attempting to create or modify them. It validates the Strand-based
    architecture is properly configured.
    """
    required_modules = [
        'orchestrator.py',
        'sourcing.py',
        'matchmaking.py',
        'collaborator.py',
        'drafting.py'
    ]
    
    print(f"Verifying Strand agent modules in: {agent_service_path}")
    
    if not os.path.exists(agent_service_path):
        print(f"  ❌ Agent service directory not found: {agent_service_path}")
        return False
    
    missing_modules = []
    for module in required_modules:
        module_path = os.path.join(agent_service_path, module)
        if os.path.exists(module_path):
            print(f"  ✓ Found: {module}")
        else:
            print(f"  ❌ Missing: {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing required agent modules: {', '.join(missing_modules)}")
        return False
    
    print("  ✓ All required agent modules are present")
    return True

def verify_aws_credentials(region_arg: str = None) -> bool:
    """
    Verify that AWS credentials are configured for Bedrock Runtime API access.
    
    This function checks environment variables without creating or modifying
    AWS resources. It validates credentials needed for Strand agents to invoke
    Claude models via the Bedrock Runtime API.
    """
    print("\nVerifying AWS credentials for Bedrock Runtime API...")
    
    # Check AWS_REGION with fallback to --region argument
    aws_region = os.environ.get('AWS_REGION')
    if aws_region:
        print(f"  ✓ AWS_REGION is set: {aws_region}")
    elif region_arg:
        print(f"  ✓ Using --region argument: {region_arg}")
        os.environ['AWS_REGION'] = region_arg  # Set it for runtime use
    else:
        print(f"  ❌ AWS_REGION is not set and no --region argument provided")
        print("Please set AWS_REGION environment variable or use --region argument")
        return False
    
    # Check other required credentials
    required_creds = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = []
    
    for var in required_creds:
        if os.environ.get(var):
            print(f"  ✓ {var} is set")
        else:
            print(f"  ❌ {var} is not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables for Bedrock Runtime API access")
        return False
    
    print("  ✓ AWS credentials are configured")
    return True

def verify_dependencies(agent_service_path: str) -> bool:
    """
    Verify that agent service dependencies file exists.
    
    This function checks for the presence of requirements.txt without
    installing or modifying dependencies.
    """
    print("\nVerifying agent service dependencies...")
    
    requirements_path = os.path.join(os.path.dirname(agent_service_path), 'requirements.txt')
    
    if os.path.exists(requirements_path):
        print(f"  ✓ Found: requirements.txt")
        return True
    else:
        print(f"  ⚠ Warning: requirements.txt not found at {requirements_path}")
        print("  Make sure agent service dependencies are installed")
        return True  # Non-fatal warning

def verify_fastapi_health(service_url: str = 'http://localhost:8001') -> bool:
    """
    Optional health check for FastAPI service.
    
    This function attempts to verify the FastAPI agent service is running
    by checking its /health endpoint. This is non-fatal if the service
    is not currently running.
    """
    print("\nChecking FastAPI service health (optional)...")
    
    try:
        import urllib.request
        import urllib.error
        
        health_url = f"{service_url}/health"
        req = urllib.request.Request(health_url, method='GET')
        
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print(f"  ✓ FastAPI service is running at {service_url}")
                return True
            else:
                print(f"  ⚠ FastAPI service returned status {response.status}")
                return False
    except urllib.error.URLError:
        print(f"  ⚠ FastAPI service is not running at {service_url}")
        print("  This is optional - start the service with: cd agent-service && python main.py")
        return False
    except Exception as e:
        print(f"  ⚠ Could not check FastAPI service: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Verify Strand Agent Configuration for FundingForge')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--model', default='anthropic.claude-3-5-sonnet-20241022-v2:0', 
                       help='Foundation model ID')
    parser.add_argument('--agent-service-path', default='agent-service/agents',
                       help='Path to agent service directory')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Strand Agent Configuration Verification")
    print("=" * 60)
    print()
    
    print(f"Region: {args.region}")
    print(f"Model: {args.model}")
    print(f"Agent Service Path: {args.agent_service_path}")
    print()
    
    # Verify agent modules
    if not verify_agent_modules(args.agent_service_path):
        sys.exit(1)
    
    # Verify AWS credentials (with --region as fallback)
    if not verify_aws_credentials(args.region):
        sys.exit(1)
    
    # Verify dependencies
    verify_dependencies(args.agent_service_path)
    
    # Optional: Check if FastAPI service is running
    verify_fastapi_health()
    
    # Generate Strand-based configuration
    config = {
        'architecture': 'strand-fastapi',
        'agentServiceUrl': 'http://localhost:8001',
        'agentServiceEndpoint': '/invoke',
        'requiredAgents': [
            'orchestrator',
            'sourcing',
            'matchmaking',
            'collaborator',
            'drafting'
        ],
        'bedrockRuntimeConfig': {
            'region': args.region,
            'model': args.model
        }
    }
    
    # Save configuration
    with open('agent_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Strand Agent Configuration Verified Successfully!")
    print("=" * 60)
    print(f"\nConfiguration saved to: agent_config.json")
    print("\nVerified Strand agents:")
    for agent in config['requiredAgents']:
        print(f"  - {agent}")
    print("\nAgent Service Configuration:")
    print(f"  URL: {config['agentServiceUrl']}")
    print(f"  Endpoint: {config['agentServiceEndpoint']}")
    print(f"  Architecture: {config['architecture']}")
    print("\nNext steps:")
    print("  1. Start the FastAPI agent service: cd agent-service && python main.py")
    print("  2. Start the Express backend: npm run dev")
    print("\nNote: This script verifies configuration only. It does not create")
    print("      or modify AWS Bedrock agents. The Strand-based architecture")
    print("      uses direct model invocation via the Bedrock Runtime API.")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Verification Error: {e}", file=sys.stderr)
        print("\nThe Strand agent configuration could not be verified.", file=sys.stderr)
        print("Please check that all required agent modules and AWS credentials are present.", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
