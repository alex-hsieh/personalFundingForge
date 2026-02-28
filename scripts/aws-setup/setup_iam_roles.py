#!/usr/bin/env python3
"""
Setup IAM Roles for Bedrock Agents Migration

Creates all necessary IAM roles with least-privilege policies for:
- Supervisor Agent
- Sub-Agents (Sourcing, Matchmaking, Collaborator, Drafting)
- Knowledge Base
- Lambda Action Groups
- Express Backend
"""

import boto3
import json
import argparse
import sys
from typing import Dict, Any

def create_iam_client(region: str):
    """Initialize IAM client"""
    return boto3.client('iam', region_name=region)

def create_trust_policy(service: str) -> Dict[str, Any]:
    """Create trust policy for AWS service"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": service
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

def create_supervisor_agent_role(iam_client, account_id: str, region: str) -> str:
    """Create IAM role for Supervisor Agent"""
    role_name = "FundingForge-SupervisorAgent-Role"
    
    print(f"Creating IAM role: {role_name}")
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(create_trust_policy("bedrock.amazonaws.com")),
            Description="IAM role for FundingForge Supervisor Agent",
            Tags=[
                {'Key': 'Project', 'Value': 'FundingForge'},
                {'Key': 'Component', 'Value': 'SupervisorAgent'}
            ]
        )
        role_arn = response['Role']['Arn']
        
        # Create inline policy for invoking sub-agents
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeAgent"],
                    "Resource": [
                        f"arn:aws:bedrock:{region}:{account_id}:agent/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock/agents/*"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="SupervisorAgentPolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✓ Created Supervisor Agent role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✓ Role {role_name} already exists")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']

def create_sub_agent_role(iam_client, agent_name: str, account_id: str, region: str, 
                          needs_kb: bool = False, lambda_arns: list = None) -> str:
    """Create IAM role for Sub-Agent"""
    role_name = f"FundingForge-{agent_name}Agent-Role"
    
    print(f"Creating IAM role: {role_name}")
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(create_trust_policy("bedrock.amazonaws.com")),
            Description=f"IAM role for FundingForge {agent_name} Agent",
            Tags=[
                {'Key': 'Project', 'Value': 'FundingForge'},
                {'Key': 'Component', 'Value': f'{agent_name}Agent'}
            ]
        )
        role_arn = response['Role']['Arn']
        
        # Base policy for all sub-agents
        statements = [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock/agents/*"
            }
        ]
        
        # Add Knowledge Base permissions if needed
        if needs_kb:
            statements.append({
                "Effect": "Allow",
                "Action": ["bedrock:Retrieve"],
                "Resource": f"arn:aws:bedrock:{region}:{account_id}:knowledge-base/*"
            })
        
        # Add Lambda invocation permissions if needed
        if lambda_arns:
            statements.append({
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": lambda_arns
            })
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": statements
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{agent_name}AgentPolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✓ Created {agent_name} Agent role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✓ Role {role_name} already exists")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']

def create_knowledge_base_role(iam_client, account_id: str, region: str) -> str:
    """Create IAM role for Knowledge Base"""
    role_name = "FundingForge-KnowledgeBase-Role"
    
    print(f"Creating IAM role: {role_name}")
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(create_trust_policy("bedrock.amazonaws.com")),
            Description="IAM role for FundingForge Knowledge Base",
            Tags=[
                {'Key': 'Project', 'Value': 'FundingForge'},
                {'Key': 'Component', 'Value': 'KnowledgeBase'}
            ]
        )
        role_arn = response['Role']['Arn']
        
        # Policy for Knowledge Base
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::fundingforge-knowledge-base",
                        f"arn:aws:s3:::fundingforge-knowledge-base/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:APIAccessAll"
                    ],
                    "Resource": f"arn:aws:aoss:{region}:{account_id}:collection/*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="KnowledgeBasePolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"✓ Created Knowledge Base role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✓ Role {role_name} already exists")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']

def create_lambda_execution_role(iam_client, function_name: str, account_id: str, region: str) -> str:
    """Create IAM role for Lambda function"""
    role_name = f"FundingForge-{function_name}-Lambda-Role"
    
    print(f"Creating IAM role: {role_name}")
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(create_trust_policy("lambda.amazonaws.com")),
            Description=f"IAM role for FundingForge {function_name} Lambda",
            Tags=[
                {'Key': 'Project', 'Value': 'FundingForge'},
                {'Key': 'Component', 'Value': f'{function_name}Lambda'}
            ]
        )
        role_arn = response['Role']['Arn']
        
        # Attach AWS managed policy for Lambda basic execution
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        print(f"✓ Created {function_name} Lambda role: {role_arn}")
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✓ Role {role_name} already exists")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']

def main():
    parser = argparse.ArgumentParser(description='Setup IAM roles for Bedrock Agents')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - IAM Roles Setup")
    print("=" * 60)
    print()
    
    # Initialize clients
    iam_client = create_iam_client(args.region)
    sts_client = boto3.client('sts')
    
    # Get account ID
    account_id = sts_client.get_caller_identity()['Account']
    print(f"AWS Account ID: {account_id}")
    print(f"Region: {args.region}")
    print()
    
    # Create roles
    config = {
        'account_id': account_id,
        'region': args.region,
        'roles': {}
    }
    
    # 1. Supervisor Agent Role
    print("\n1. Creating Supervisor Agent Role...")
    config['roles']['supervisor'] = create_supervisor_agent_role(iam_client, account_id, args.region)
    
    # 2. Sub-Agent Roles
    print("\n2. Creating Sub-Agent Roles...")
    
    # Sourcing Agent (no special permissions)
    config['roles']['sourcing'] = create_sub_agent_role(
        iam_client, "Sourcing", account_id, args.region
    )
    
    # Matchmaking Agent (needs Knowledge Base access)
    config['roles']['matchmaking'] = create_sub_agent_role(
        iam_client, "Matchmaking", account_id, args.region, needs_kb=True
    )
    
    # Collaborator Agent (will need Lambda ARN later)
    config['roles']['collaborator'] = create_sub_agent_role(
        iam_client, "Collaborator", account_id, args.region
    )
    
    # Drafting Agent (will need Lambda ARN later)
    config['roles']['drafting'] = create_sub_agent_role(
        iam_client, "Drafting", account_id, args.region
    )
    
    # 3. Knowledge Base Role
    print("\n3. Creating Knowledge Base Role...")
    config['roles']['knowledge_base'] = create_knowledge_base_role(iam_client, account_id, args.region)
    
    # 4. Lambda Execution Roles
    print("\n4. Creating Lambda Execution Roles...")
    config['roles']['lambda_faculty_ranking'] = create_lambda_execution_role(
        iam_client, "FacultyRanking", account_id, args.region
    )
    config['roles']['lambda_compliance_checker'] = create_lambda_execution_role(
        iam_client, "ComplianceChecker", account_id, args.region
    )
    config['roles']['lambda_proposal_formatter'] = create_lambda_execution_role(
        iam_client, "ProposalFormatter", account_id, args.region
    )
    
    # Save configuration
    with open('iam_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ IAM Roles Setup Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: iam_config.json")
    print("\nNext steps:")
    print("1. Run: python setup_knowledge_base.py --region", args.region)
    print("2. Run: python deploy_lambda_functions.py --region", args.region)
    print("3. Run: python setup_bedrock_agents.py --region", args.region)
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
