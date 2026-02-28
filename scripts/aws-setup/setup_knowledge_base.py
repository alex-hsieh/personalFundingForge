#!/usr/bin/env python3
"""
Setup Knowledge Base for Bedrock Agents Migration

Creates:
- S3 bucket for grant documents
- OpenSearch Serverless collection for vector storage
- Bedrock Knowledge Base with data source
"""

import boto3
import json
import argparse
import sys
import time
from typing import Dict, Any

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

def create_opensearch_collection(aoss_client, collection_name: str, account_id: str) -> Dict[str, str]:
    """Create OpenSearch Serverless collection"""
    print(f"Creating OpenSearch Serverless collection: {collection_name}")
    
    try:
        # Create encryption policy
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AWSOwnedKey": True
        }
        
        try:
            aoss_client.create_security_policy(
                name=f"{collection_name}-encryption",
                type='encryption',
                policy=json.dumps(encryption_policy)
            )
        except aoss_client.exceptions.ConflictException:
            print(f"  Encryption policy already exists")
        
        # Create network policy (public access for now)
        network_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    },
                    {
                        "ResourceType": "dashboard",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AllowFromPublic": True
            }
        ]
        
        try:
            aoss_client.create_security_policy(
                name=f"{collection_name}-network",
                type='network',
                policy=json.dumps(network_policy)
            )
        except aoss_client.exceptions.ConflictException:
            print(f"  Network policy already exists")
        
        # Create data access policy
        data_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ]
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument"
                        ]
                    }
                ],
                "Principal": [f"arn:aws:iam::{account_id}:role/FundingForge-KnowledgeBase-Role"]
            }
        ]
        
        try:
            aoss_client.create_access_policy(
                name=f"{collection_name}-access",
                type='data',
                policy=json.dumps(data_policy)
            )
        except aoss_client.exceptions.ConflictException:
            print(f"  Access policy already exists")
        
        # Create collection
        response = aoss_client.create_collection(
            name=collection_name,
            type='VECTORSEARCH',
            description='Vector store for FundingForge Knowledge Base'
        )
        
        collection_id = response['createCollectionDetail']['id']
        collection_arn = response['createCollectionDetail']['arn']
        
        print(f"  Waiting for collection to become active...")
        while True:
            status_response = aoss_client.batch_get_collection(ids=[collection_id])
            status = status_response['collectionDetails'][0]['status']
            if status == 'ACTIVE':
                break
            print(f"  Collection status: {status}")
            time.sleep(10)
        
        # Get collection endpoint
        collection_details = aoss_client.batch_get_collection(ids=[collection_id])
        endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']
        
        print(f"✓ Created OpenSearch collection: {collection_id}")
        print(f"  Endpoint: {endpoint}")
        
        return {
            'id': collection_id,
            'arn': collection_arn,
            'endpoint': endpoint
        }
        
    except aoss_client.exceptions.ConflictException:
        print(f"✓ OpenSearch collection {collection_name} already exists")
        # Get existing collection
        collections = aoss_client.list_collections(
            collectionFilters={'name': collection_name}
        )
        if collections['collectionSummaries']:
            collection_id = collections['collectionSummaries'][0]['id']
            collection_arn = collections['collectionSummaries'][0]['arn']
            collection_details = aoss_client.batch_get_collection(ids=[collection_id])
            endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']
            return {
                'id': collection_id,
                'arn': collection_arn,
                'endpoint': endpoint
            }
        raise

def create_opensearch_index(collection_endpoint: str, index_name: str):
    """Create OpenSearch index for Knowledge Base"""
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    import boto3
    
    print(f"Creating OpenSearch index: {index_name}")
    
    # Get AWS credentials for signing requests
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        boto3.Session().region_name,
        'aoss',
        session_token=credentials.token
    )
    
    # Create OpenSearch client
    host = collection_endpoint.replace('https://', '')
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    # Define index mapping for vector search
    index_body = {
        'settings': {
            'index': {
                'knn': True,
                'knn.algo_param.ef_search': 512
            }
        },
        'mappings': {
            'properties': {
                'embedding': {
                    'type': 'knn_vector',
                    'dimension': 1024,
                    'method': {
                        'name': 'hnsw',
                        'engine': 'faiss',
                        'parameters': {
                            'ef_construction': 512,
                            'm': 16
                        }
                    }
                },
                'text': {
                    'type': 'text'
                },
                'metadata': {
                    'type': 'text'
                }
            }
        }
    }
    
    try:
        # Create index
        response = client.indices.create(index=index_name, body=index_body)
        print(f"✓ Created OpenSearch index: {index_name}")
        return True
    except Exception as e:
        if 'resource_already_exists_exception' in str(e).lower():
            print(f"✓ OpenSearch index {index_name} already exists")
            return True
        else:
            print(f"⚠️  Warning: Could not create index: {e}")
            print(f"  You may need to create it manually or install opensearch-py")
            return False

def create_knowledge_base(bedrock_client, kb_name: str, role_arn: str, 
                         collection_arn: str, collection_endpoint: str, s3_bucket: str, region: str) -> Dict[str, str]:
    """Create Bedrock Knowledge Base"""
    print(f"Creating Bedrock Knowledge Base: {kb_name}")
    
    # Try to create the OpenSearch index first
    try:
        create_opensearch_index(collection_endpoint, 'fundingforge-index')
    except ImportError:
        print("⚠️  Warning: opensearch-py not installed, skipping index creation")
        print("  Install with: pip install opensearch-py requests-aws4auth")
        print("  The Knowledge Base creation may fail if the index doesn't exist")
    except Exception as e:
        print(f"⚠️  Warning: Could not create OpenSearch index: {e}")
        print("  Proceeding anyway - Knowledge Base creation may fail")
    
    try:
        # Create Knowledge Base
        response = bedrock_client.create_knowledge_base(
            name=kb_name,
            description='Knowledge Base for FundingForge grant documents',
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': 'fundingforge-index',
                    'fieldMapping': {
                        'vectorField': 'embedding',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        kb_arn = response['knowledgeBase']['knowledgeBaseArn']
        
        print(f"✓ Created Knowledge Base: {kb_id}")
        
        # Create data source
        print(f"  Creating S3 data source...")
        ds_response = bedrock_client.create_data_source(
            knowledgeBaseId=kb_id,
            name='fundingforge-s3-source',
            description='S3 data source for grant documents',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{s3_bucket}'
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 300,
                        'overlapPercentage': 20
                    }
                }
            }
        )
        
        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"✓ Created data source: {ds_id}")
        
        return {
            'id': kb_id,
            'arn': kb_arn,
            'data_source_id': ds_id
        }
        
    except bedrock_client.exceptions.ConflictException:
        print(f"✓ Knowledge Base {kb_name} already exists")
        # List and find existing KB
        kbs = bedrock_client.list_knowledge_bases()
        for kb in kbs['knowledgeBaseSummaries']:
            if kb['name'] == kb_name:
                kb_id = kb['knowledgeBaseId']
                # Get data sources
                ds_list = bedrock_client.list_data_sources(knowledgeBaseId=kb_id)
                ds_id = ds_list['dataSourceSummaries'][0]['dataSourceId'] if ds_list['dataSourceSummaries'] else None
                return {
                    'id': kb_id,
                    'arn': kb['knowledgeBaseArn'],
                    'data_source_id': ds_id
                }
        raise

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
    
    print(f"✓ Uploaded sample documents")

def main():
    parser = argparse.ArgumentParser(description='Setup Knowledge Base for Bedrock Agents')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--skip-sample-docs', action='store_true', help='Skip uploading sample documents')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Knowledge Base Setup")
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
    
    account_id = iam_config['account_id']
    kb_role_arn = iam_config['roles']['knowledge_base']
    
    print(f"AWS Account ID: {account_id}")
    print(f"Region: {args.region}")
    print()
    
    # Initialize clients
    s3_client = boto3.client('s3', region_name=args.region)
    aoss_client = boto3.client('opensearchserverless', region_name=args.region)
    bedrock_client = boto3.client('bedrock-agent', region_name=args.region)
    
    config = {
        'region': args.region,
        'account_id': account_id
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
    
    # 3. Create OpenSearch Serverless collection
    print("\n3. Creating OpenSearch Serverless Collection...")
    collection_name = 'fundingforge-vectors'
    config['opensearch'] = create_opensearch_collection(aoss_client, collection_name, account_id)
    
    # 4. Create Knowledge Base
    print("\n4. Creating Bedrock Knowledge Base...")
    kb_name = 'FundingForgeKnowledgeBase'
    config['knowledge_base'] = create_knowledge_base(
        bedrock_client, kb_name, kb_role_arn,
        config['opensearch']['arn'], config['opensearch']['endpoint'], bucket_name, args.region
    )
    
    # 5. Start ingestion job
    print("\n5. Starting Ingestion Job...")
    if not args.skip_sample_docs:
        try:
            ingestion_response = bedrock_client.start_ingestion_job(
                knowledgeBaseId=config['knowledge_base']['id'],
                dataSourceId=config['knowledge_base']['data_source_id']
            )
            ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
            print(f"✓ Started ingestion job: {ingestion_job_id}")
            print(f"  Monitor status with: aws bedrock-agent get-ingestion-job --knowledge-base-id {config['knowledge_base']['id']} --data-source-id {config['knowledge_base']['data_source_id']} --ingestion-job-id {ingestion_job_id}")
        except Exception as e:
            print(f"  Warning: Could not start ingestion job: {e}")
    
    # Save configuration
    with open('knowledge_base_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✓ Knowledge Base Setup Complete!")
    print("=" * 60)
    print(f"\nConfiguration saved to: knowledge_base_config.json")
    print(f"\nS3 Bucket: s3://{bucket_name}")
    print(f"Knowledge Base ID: {config['knowledge_base']['id']}")
    print(f"\nTo add documents:")
    print(f"  aws s3 cp your-document.pdf s3://{bucket_name}/policies/")
    print(f"  aws bedrock-agent start-ingestion-job --knowledge-base-id {config['knowledge_base']['id']} --data-source-id {config['knowledge_base']['data_source_id']}")
    print("\nNext step:")
    print("  python deploy_lambda_functions.py --region", args.region)
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
