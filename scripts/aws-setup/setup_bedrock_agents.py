#!/usr/bin/env python3
"""
Setup Bedrock Agents for FundingForge Migration

Creates:
- Supervisor Agent (orchestrator)
- 4 Sub-Agents (Sourcing, Matchmaking, Collaborator, Drafting)
"""

import boto3
import json
import argparse
import sys
import time

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

def create_bedrock_agent(bedrock_client, agent_name: str, instructions: str, 
                        role_arn: str, model_id: str) -> dict:
    """Create a Bedrock Agent"""
    print(f"Creating Bedrock Agent: {agent_name}")
    
    try:
        response = bedrock_client.create_agent(
            agentName=agent_name,
            agentResourceRoleArn=role_arn,
            description=f'FundingForge {agent_name}',
            instruction=instructions,
            foundationModel=model_id,
            idleSessionTTLInSeconds=600
        )
        
        agent_id = response['agent']['agentId']
        agent_arn = response['agent']['agentArn']
        
        print(f"  Agent ID: {agent_id}")
        
        # Create DRAFT alias
        print(f"  Creating DRAFT alias...")
        alias_response = bedrock_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName='DRAFT',
            description='Draft alias for development'
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        
        # Prepare agent (required before use)
        print(f"  Preparing agent...")
        bedrock_client.prepare_agent(agentId=agent_id)
        
        # Wait for agent to be prepared
        time.sleep(5)
        
        print(f"✓ Created agent: {agent_name}")
        
        return {
            'id': agent_id,
            'arn': agent_arn,
            'alias_id': alias_id,
            'name': agent_name
        }
        
    except bedrock_client.exceptions.ConflictException:
        print(f"✓ Agent {agent_name} already exists")
        # List agents and find existing one
        agents = bedrock_client.list_agents()
        for agent in agents['agentSummaries']:
            if agent['agentName'] == agent_name:
                agent_id = agent['agentId']
                # Get aliases
                aliases = bedrock_client.list_agent_aliases(agentId=agent_id)
                alias_id = None
                for alias in aliases['agentAliasSummaries']:
                    if alias['agentAliasName'] == 'DRAFT':
                        alias_id = alias['agentAliasId']
                        break
                return {
                    'id': agent_id,
                    'arn': f"arn:aws:bedrock:{bedrock_client.meta.region_name}:{boto3.client('sts').get_caller_identity()['Account']}:agent/{agent_id}",
                    'alias_id': alias_id,
                    'name': agent_name
                }
        raise

def main():
    parser = argparse.ArgumentParser(description='Setup Bedrock Agents for FundingForge')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--model', default='anthropic.claude-3-5-sonnet-20241022-v2:0', 
                       help='Foundation model ID')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Bedrock Agents Setup")
    print("=" * 60)
    print()
    
    # Load IAM config
    try:
        with open('iam_config.json', 'r') as f:
            iam_config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: iam_config.json not found")
        print("Please run: python setup_iam_roles.py first")
        sys.exit(1)
    
    print(f"Region: {args.region}")
    print(f"Model: {args.model}")
    print()
    
    # Initialize Bedrock client
    bedrock_client = boto3.client('bedrock-agent', region_name=args.region)
    
    config = {
        'region': args.region,
        'model': args.model,
        'agents': {}
    }
    
    # 1. Create Supervisor Agent
    print("\n1. Creating Supervisor Agent...")
    config['agents']['supervisor'] = create_bedrock_agent(
        bedrock_client,
        'FundingForge-Supervisor',
        SUPERVISOR_INSTRUCTIONS,
        iam_config['roles']['supervisor'],
        args.model
    )
    
    # 2. Create Sourcing Agent
    print("\n2. Creating Sourcing Agent...")
    config['agents']['sourcing'] = create_bedrock_agent(
        bedrock_client,
        'FundingForge-Sourcing',
        SOURCING_INSTRUCTIONS,
        iam_config['roles']['sourcing'],
        args.model
    )
    
    # 3. Create Matchmaking Agent
    print("\n3. Creating Matchmaking Agent...")
    config['agents']['matchmaking'] = create_bedrock_agent(
        bedrock_client,
        'FundingForge-Matchmaking',
        MATCHMAKING_INSTRUCTIONS,
        iam_config['roles']['matchmaking'],
        args.model
    )
    
    # 4. Create Collaborator Agent
    print("\n4. Creating Collaborator Agent...")
    config['agents']['collaborator'] = create_bedrock_agent(
        bedrock_client,
        'FundingForge-Collaborator',
        COLLABORATOR_INSTRUCTIONS,
        iam_config['roles']['collaborator'],
        args.model
    )
    
    # 5. Create Drafting Agent
    print("\n5. Creating Drafting Agent...")
    config['agents']['drafting'] = create_bedrock_agent(
        bedrock_client,
        'FundingForge-Drafting',
        DRAFTING_INSTRUCTIONS,
        iam_config['roles']['drafting'],
        args.model
    )
    
    # Save configuration
    with open('agent_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Bedrock Agents Setup Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: agent_config.json")
    print("\nCreated agents:")
    for agent_type, agent_info in config['agents'].items():
        print(f"  {agent_type}: {agent_info['id']}")
    print("\nNext step:")
    print("  python link_action_groups.py --region", args.region)
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
