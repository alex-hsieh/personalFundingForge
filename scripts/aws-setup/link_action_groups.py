#!/usr/bin/env python3
"""
Link Lambda Action Groups to Bedrock Agents

Links:
- Faculty Ranking Lambda → Collaborator Agent
- Compliance Checker Lambda → Matchmaking Agent  
- Proposal Formatter Lambda → Drafting Agent
"""

import boto3
import json
import argparse
import sys
import time

def link_action_group(bedrock_client, agent_id: str, action_group_name: str,
                     lambda_arn: str, openapi_schema: dict) -> str:
    """Link an action group to a Bedrock Agent"""
    print(f"Linking action group: {action_group_name} to agent {agent_id}")
    
    try:
        response = bedrock_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=action_group_name,
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(openapi_schema)
            },
            description=f'Action group for {action_group_name}'
        )
        
        action_group_id = response['agentActionGroup']['actionGroupId']
        print(f"✓ Linked action group: {action_group_id}")
        
        return action_group_id
        
    except bedrock_client.exceptions.ConflictException:
        print(f"✓ Action group {action_group_name} already linked")
        # List action groups and find existing one
        action_groups = bedrock_client.list_agent_action_groups(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        for ag in action_groups['actionGroupSummaries']:
            if ag['actionGroupName'] == action_group_name:
                return ag['actionGroupId']
        raise

def add_lambda_permission(lambda_client, function_name: str, agent_id: str, region: str, account_id: str):
    """Add permission for Bedrock Agent to invoke Lambda"""
    print(f"  Adding Lambda permission for agent {agent_id}")
    
    statement_id = f"bedrock-agent-{agent_id}"
    
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f'arn:aws:bedrock:{region}:{account_id}:agent/{agent_id}'
        )
        print(f"  ✓ Added Lambda permission")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"  ✓ Lambda permission already exists")

def link_knowledge_base(bedrock_client, agent_id: str, kb_id: str):
    """Link Knowledge Base to Bedrock Agent"""
    print(f"Linking Knowledge Base {kb_id} to agent {agent_id}")
    
    try:
        response = bedrock_client.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            knowledgeBaseId=kb_id,
            description='FundingForge Knowledge Base for compliance documents',
            knowledgeBaseState='ENABLED'
        )
        
        print(f"✓ Linked Knowledge Base")
        return response['agentKnowledgeBase']['agentKnowledgeBaseId']
        
    except bedrock_client.exceptions.ConflictException:
        print(f"✓ Knowledge Base already linked")
        # List knowledge bases and find existing one
        kbs = bedrock_client.list_agent_knowledge_bases(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        if kbs['agentKnowledgeBaseSummaries']:
            return kbs['agentKnowledgeBaseSummaries'][0]['agentKnowledgeBaseId']
        raise

def main():
    parser = argparse.ArgumentParser(description='Link Action Groups to Bedrock Agents')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Link Action Groups")
    print("=" * 60)
    print()
    
    # Load configurations
    try:
        with open('agent_config.json', 'r') as f:
            agent_config = json.load(f)
        with open('lambda_config.json', 'r') as f:
            lambda_config = json.load(f)
        with open('iam_config.json', 'r') as f:
            iam_config = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: Configuration file not found: {e.filename}")
        print("Please run the setup scripts in order:")
        print("  1. python setup_iam_roles.py")
        print("  2. python deploy_lambda_functions.py")
        print("  3. python setup_bedrock_agents.py")
        sys.exit(1)
    
    # Try to load Knowledge Base config (optional)
    kb_config = None
    try:
        with open('knowledge_base_config.json', 'r') as f:
            kb_config = json.load(f)
    except FileNotFoundError:
        print("⚠️  Warning: knowledge_base_config.json not found")
        print("  Knowledge Base will not be linked to Matchmaking Agent")
        print("  Run: python setup_knowledge_base.py if you want KB integration")
        print()
    
    account_id = iam_config['account_id']
    print(f"Region: {args.region}")
    print()
    
    # Initialize clients
    bedrock_client = boto3.client('bedrock-agent', region_name=args.region)
    lambda_client = boto3.client('lambda', region_name=args.region)
    
    config = {
        'region': args.region,
        'linked_action_groups': {}
    }
    
    # 1. Link Faculty Ranking to Collaborator Agent
    print("\n1. Linking Faculty Ranking to Collaborator Agent...")
    collaborator_id = agent_config['agents']['collaborator']['id']
    faculty_ranking_arn = lambda_config['functions']['faculty_ranking']['arn']
    faculty_ranking_schema = lambda_config['functions']['faculty_ranking']['openapi_schema']
    
    add_lambda_permission(lambda_client, 'FundingForge-FacultyRanking', 
                         collaborator_id, args.region, account_id)
    
    config['linked_action_groups']['faculty_ranking'] = link_action_group(
        bedrock_client, collaborator_id, 'FacultyRanking',
        faculty_ranking_arn, faculty_ranking_schema
    )
    
    # 2. Link Compliance Checker to Matchmaking Agent
    print("\n2. Linking Compliance Checker to Matchmaking Agent...")
    matchmaking_id = agent_config['agents']['matchmaking']['id']
    compliance_checker_arn = lambda_config['functions']['compliance_checker']['arn']
    compliance_checker_schema = lambda_config['functions']['compliance_checker']['openapi_schema']
    
    add_lambda_permission(lambda_client, 'FundingForge-ComplianceChecker',
                         matchmaking_id, args.region, account_id)
    
    config['linked_action_groups']['compliance_checker'] = link_action_group(
        bedrock_client, matchmaking_id, 'ComplianceChecker',
        compliance_checker_arn, compliance_checker_schema
    )
    
    # 3. Link Proposal Formatter to Drafting Agent
    print("\n3. Linking Proposal Formatter to Drafting Agent...")
    drafting_id = agent_config['agents']['drafting']['id']
    proposal_formatter_arn = lambda_config['functions']['proposal_formatter']['arn']
    proposal_formatter_schema = lambda_config['functions']['proposal_formatter']['openapi_schema']
    
    add_lambda_permission(lambda_client, 'FundingForge-ProposalFormatter',
                         drafting_id, args.region, account_id)
    
    config['linked_action_groups']['proposal_formatter'] = link_action_group(
        bedrock_client, drafting_id, 'ProposalFormatter',
        proposal_formatter_arn, proposal_formatter_schema
    )
    
    # 4. Link Knowledge Base to Matchmaking Agent (if available)
    if kb_config:
        print("\n4. Linking Knowledge Base to Matchmaking Agent...")
        kb_id = kb_config['knowledge_base']['id']
        config['knowledge_base_link'] = link_knowledge_base(
            bedrock_client, matchmaking_id, kb_id
        )
    
    # 5. Prepare all agents (required after modifications)
    print("\n5. Preparing all agents...")
    for agent_type, agent_info in agent_config['agents'].items():
        print(f"  Preparing {agent_type} agent...")
        bedrock_client.prepare_agent(agentId=agent_info['id'])
        time.sleep(2)
    
    print("  ✓ All agents prepared")
    
    # Save configuration
    with open('action_groups_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Action Groups Linking Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: action_groups_config.json")
    print("\nLinked action groups:")
    for ag_name, ag_id in config['linked_action_groups'].items():
        print(f"  {ag_name}: {ag_id}")
    print("\nNext step:")
    print("  python generate_env_file.py")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
