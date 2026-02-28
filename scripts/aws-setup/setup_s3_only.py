#!/usr/bin/env python3
"""
Setup S3-Only Knowledge Base (No OpenSearch)

Creates S3 bucket for grant documents without the complexity of OpenSearch Serverless.
The Matchmaking Agent will retrieve documents directly from S3.
"""

import boto3
import json
import argparse
import sys

def create_s3_bucket(s3_client, bucket_name: str, region: str) -> str:
    """Create S3 bucket with versioning and encryption"""
    print(f"Creating S3 bucket: {bucket_name}")
    
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Enable encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
        
        # Create directory structure
        for prefix in ['policies/', 'templates/', 'compliance/']:
            s3_client.put_object(Bucket=bucket_name, Key=prefix)
        
        print(f"✓ Created S3 bucket: s3://{bucket_name}")
        return f"arn:aws:s3:::{bucket_name}"
        
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ S3 bucket {bucket_name} already exists")
        return f"arn:aws:s3:::{bucket_name}"

def upload_sample_documents(s3_client, bucket_name: str):
    """Upload sample grant documents"""
    print(f"Uploading sample documents to S3...")
    
    # Sample policy document
    policy_doc = """
    FSU Grant Submission Policy
    
    All grant proposals must be submitted through the Research Administration and Management Portal (RAMP).
    
    Requirements:
    1. Complete RAMP proposal form
    2. Obtain department chair approval
    3. Submit Conflict of Interest (COI) disclosure
    4. Include IRB approval if human subjects research
    5. Attach budget justification
    
    Timeline:
    - Internal deadline: 5 business days before sponsor deadline
    - RAMP submission: 3 business days before sponsor deadline
    """
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key='policies/grant_submission_policy.txt',
        Body=policy_doc.encode('utf-8'),
        ContentType='text/plain'
    )
    
    # Sample compliance document
    compliance_doc = """
    FSU Compliance Requirements
    
    RAMP (Research Administration and Management Portal):
    - All proposals must be entered in RAMP
    - Budget must be reviewed by Office of Research
    - Institutional approvals required before submission
    
    COI (Conflict of Interest):
    - Annual disclosure required for all PIs
    - Update within 30 days of new financial interests
    - Managed through COI disclosure system
    
    IRB (Institutional Review Board):
    - Required for human subjects research
    - Submit protocol before data collection
    - Annual renewal required for ongoing studies
    
    Policy Compliance:
    - Follow FSU research policies
    - Comply with sponsor requirements
    - Maintain proper documentation
    """
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key='compliance/compliance_requirements.txt',
        Body=compliance_doc.encode('utf-8'),
        ContentType='text/plain'
    )
    
    # Sample template
    template_doc = """
    Grant Proposal Template
    
    1. Executive Summary
       - Brief overview of the project
       - Key objectives and expected outcomes
    
    2. Principal Investigator Qualifications
       - Education and experience
       - Relevant publications and grants
    
    3. Project Description
       - Background and significance
       - Research methodology
       - Timeline and milestones
    
    4. Budget and Justification
       - Personnel costs
       - Equipment and supplies
       - Travel and other expenses
    
    5. Broader Impacts
       - Educational outreach
       - Community engagement
       - Diversity and inclusion
    """
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key='templates/proposal_template.txt',
        Body=template_doc.encode('utf-8'),
        ContentType='text/plain'
    )
    
    print(f"✓ Uploaded sample documents")

def update_iam_role_for_s3(iam_client, role_name: str, bucket_name: str, region: str):
    """Update Matchmaking Agent IAM role to allow S3 access"""
    print(f"Updating IAM role {role_name} for S3 access...")
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "bedrock:InvokeModel",
                "Resource": f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{region}:*:log-group:/aws/bedrock/agents/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="MatchmakingAgentPolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        print(f"✓ Updated IAM role with S3 permissions")
    except Exception as e:
        print(f"⚠️  Warning: Could not update IAM role: {e}")

def main():
    parser = argparse.ArgumentParser(description='Setup S3-only knowledge base')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--skip-sample-docs', action='store_true', help='Skip uploading sample documents')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - S3-Only Knowledge Base Setup")
    print("=" * 60)
    print()
    print("This setup uses S3 directly without OpenSearch Serverless")
    print("Benefits: Simpler, cheaper, faster, less process-intensive")
    print()
    
    # Load IAM config
    try:
        with open('iam_config.json', 'r') as f:
            iam_config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: iam_config.json not found")
        print("Please run: python setup_iam_roles.py first")
        sys.exit(1)
    
    account_id = iam_config['account_id']
    
    print(f"AWS Account ID: {account_id}")
    print(f"Region: {args.region}")
    print()
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=args.region)
    iam_client = boto3.client('iam', region_name=args.region)
    
    config = {
        'region': args.region,
        'account_id': account_id,
        'storage_type': 's3_only'
    }
    
    # 1. Create S3 bucket
    print("\n1. Creating S3 Bucket...")
    bucket_name = 'fundingforge-knowledge-base'
    config['s3_bucket'] = bucket_name
    config['s3_arn'] = create_s3_bucket(s3_client, bucket_name, args.region)
    
    # 2. Upload sample documents
    if not args.skip_sample_docs:
        print("\n2. Uploading Sample Documents...")
        upload_sample_documents(s3_client, bucket_name)
    
    # 3. Update Matchmaking Agent IAM role
    print("\n3. Updating Matchmaking Agent IAM Role...")
    update_iam_role_for_s3(iam_client, 'FundingForge-MatchmakingAgent-Role', bucket_name, args.region)
    
    # Save configuration
    with open('s3_knowledge_base_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ S3-Only Knowledge Base Setup Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: s3_knowledge_base_config.json")
    print(f"\nS3 Bucket: s3://{bucket_name}")
    print(f"\nTo add documents:")
    print(f"  aws s3 cp your-document.pdf s3://{bucket_name}/policies/")
    print(f"  aws s3 cp your-template.docx s3://{bucket_name}/templates/")
    print(f"  aws s3 cp your-compliance.txt s3://{bucket_name}/compliance/")
    print("\nNext step:")
    print("  python deploy_lambda_functions.py --region", args.region)
    print()
    print("Note: The Matchmaking Agent will retrieve documents directly from S3")
    print("      No vector database or embeddings needed!")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
