#!/usr/bin/env python3
"""
Deploy Lambda Functions for Bedrock Agents Migration

Deploys three Lambda Action Groups:
- Faculty Ranking
- Compliance Checker
- Proposal Formatter
"""

import boto3
import json
import argparse
import sys
import zipfile
import io
import os
from pathlib import Path

def create_lambda_deployment_package(function_code: str) -> bytes:
    """Create a ZIP deployment package for Lambda"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', function_code)
    return zip_buffer.getvalue()

def deploy_lambda_function(lambda_client, function_name: str, role_arn: str, 
                          code_path: str, memory: int, timeout: int) -> str:
    """Deploy a Lambda function"""
    print(f"Deploying Lambda function: {function_name}")
    
    # Read function code
    with open(code_path, 'r') as f:
        function_code = f.read()
    
    # Create deployment package
    zip_content = create_lambda_deployment_package(function_code)
    
    try:
        # Create function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description=f'FundingForge {function_name} Action Group',
            Timeout=timeout,
            MemorySize=memory,
            Tags={
                'Project': 'FundingForge',
                'Component': 'ActionGroup'
            }
        )
        
        function_arn = response['FunctionArn']
        print(f"✓ Created Lambda function: {function_arn}")
        return function_arn
        
    except lambda_client.exceptions.ResourceConflictException:
        print(f"  Function {function_name} already exists, updating code...")
        
        # Update function code
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Role=role_arn,
            Timeout=timeout,
            MemorySize=memory
        )
        
        # Get function ARN
        response = lambda_client.get_function(FunctionName=function_name)
        function_arn = response['Configuration']['FunctionArn']
        print(f"✓ Updated Lambda function: {function_arn}")
        return function_arn

def create_openapi_schema(function_name: str, operation_id: str, 
                         parameters: dict, description: str) -> dict:
    """Create OpenAPI 3.0 schema for Lambda Action Group"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": f"{function_name} API",
            "version": "1.0.0",
            "description": description
        },
        "paths": {
            f"/{operation_id}": {
                "post": {
                    "summary": description,
                    "operationId": operation_id,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": parameters,
                                    "required": list(parameters.keys())
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

def main():
    parser = argparse.ArgumentParser(description='Deploy Lambda functions for Bedrock Agents')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Lambda Functions Deployment")
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
    print()
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name=args.region)
    
    config = {
        'region': args.region,
        'functions': {}
    }
    
    # Get Lambda function code directory
    lambda_dir = Path(__file__).parent / 'lambda_functions'
    
    # 1. Deploy Faculty Ranking Lambda
    print("\n1. Deploying Faculty Ranking Lambda...")
    faculty_ranking_arn = deploy_lambda_function(
        lambda_client,
        'FundingForge-FacultyRanking',
        iam_config['roles']['lambda_faculty_ranking'],
        str(lambda_dir / 'faculty_ranking.py'),
        memory=512,
        timeout=30
    )
    
    config['functions']['faculty_ranking'] = {
        'arn': faculty_ranking_arn,
        'name': 'FundingForge-FacultyRanking',
        'openapi_schema': create_openapi_schema(
            'Faculty Ranking',
            'rankFaculty',
            {
                'facultyList': {
                    'type': 'array',
                    'description': 'List of faculty members',
                    'items': {'type': 'object'}
                },
                'grantRequirements': {
                    'type': 'string',
                    'description': 'Grant requirements text'
                },
                'userExpertise': {
                    'type': 'array',
                    'description': 'User expertise areas',
                    'items': {'type': 'string'}
                }
            },
            'Rank faculty members by expertise match'
        )
    }
    
    # 2. Deploy Compliance Checker Lambda
    print("\n2. Deploying Compliance Checker Lambda...")
    compliance_checker_arn = deploy_lambda_function(
        lambda_client,
        'FundingForge-ComplianceChecker',
        iam_config['roles']['lambda_compliance_checker'],
        str(lambda_dir / 'compliance_checker.py'),
        memory=256,
        timeout=15
    )
    
    config['functions']['compliance_checker'] = {
        'arn': compliance_checker_arn,
        'name': 'FundingForge-ComplianceChecker',
        'openapi_schema': create_openapi_schema(
            'Compliance Checker',
            'checkCompliance',
            {
                'checklistItems': {
                    'type': 'array',
                    'description': 'Compliance checklist items',
                    'items': {'type': 'object'}
                },
                'grantType': {
                    'type': 'string',
                    'description': 'Type of grant'
                }
            },
            'Validate compliance checklist items'
        )
    }
    
    # 3. Deploy Proposal Formatter Lambda
    print("\n3. Deploying Proposal Formatter Lambda...")
    proposal_formatter_arn = deploy_lambda_function(
        lambda_client,
        'FundingForge-ProposalFormatter',
        iam_config['roles']['lambda_proposal_formatter'],
        str(lambda_dir / 'proposal_formatter.py'),
        memory=256,
        timeout=15
    )
    
    config['functions']['proposal_formatter'] = {
        'arn': proposal_formatter_arn,
        'name': 'FundingForge-ProposalFormatter',
        'openapi_schema': create_openapi_schema(
            'Proposal Formatter',
            'formatProposal',
            {
                'proposalText': {
                    'type': 'string',
                    'description': 'Raw proposal text'
                },
                'grantName': {
                    'type': 'string',
                    'description': 'Name of the grant'
                },
                'formatStyle': {
                    'type': 'string',
                    'description': 'Formatting style (standard, academic, etc.)'
                }
            },
            'Format proposal draft with proper structure'
        )
    }
    
    # Save configuration
    with open('lambda_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Save OpenAPI schemas to separate files
    for func_name, func_config in config['functions'].items():
        schema_file = f'openapi_{func_name}.json'
        with open(schema_file, 'w') as f:
            json.dump(func_config['openapi_schema'], f, indent=2)
        print(f"  Saved OpenAPI schema: {schema_file}")
    
    print("\n" + "=" * 60)
    print("✓ Lambda Functions Deployment Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: lambda_config.json")
    print("\nDeployed functions:")
    print(f"  1. Faculty Ranking: {faculty_ranking_arn}")
    print(f"  2. Compliance Checker: {compliance_checker_arn}")
    print(f"  3. Proposal Formatter: {proposal_formatter_arn}")
    print("\nNext step:")
    print("  python setup_bedrock_agents.py --region", args.region)
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
