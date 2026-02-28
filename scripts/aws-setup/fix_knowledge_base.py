#!/usr/bin/env python3
"""
Fix Knowledge Base Setup - Create OpenSearch Index

This script creates the missing OpenSearch index that caused the Knowledge Base creation to fail.
Run this after the OpenSearch collection is created but before creating the Knowledge Base.
"""

import boto3
import json
import argparse
import sys

def create_opensearch_index(collection_endpoint: str, index_name: str):
    """Create OpenSearch index for Knowledge Base"""
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
    except ImportError:
        print("❌ Error: Required packages not installed")
        print("Install with: pip install opensearch-py requests-aws4auth")
        sys.exit(1)
    
    print(f"Creating OpenSearch index: {index_name}")
    print(f"Collection endpoint: {collection_endpoint}")
    
    # Get AWS credentials for signing requests
    session = boto3.Session()
    credentials = session.get_credentials()
    region = session.region_name or 'us-east-1'
    
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
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
            raise

def main():
    parser = argparse.ArgumentParser(description='Fix Knowledge Base by creating OpenSearch index')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Fix Knowledge Base Setup")
    print("=" * 60)
    print()
    
    # Load knowledge base config to get collection endpoint
    try:
        with open('knowledge_base_config.json', 'r') as f:
            kb_config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: knowledge_base_config.json not found")
        print("This script should be run after OpenSearch collection is created")
        print("but before Knowledge Base creation")
        sys.exit(1)
    
    collection_endpoint = kb_config['opensearch']['endpoint']
    
    print(f"Region: {args.region}")
    print(f"Collection endpoint: {collection_endpoint}")
    print()
    
    # Create the index
    try:
        create_opensearch_index(collection_endpoint, 'fundingforge-index')
        print("\n✓ OpenSearch index created successfully!")
        print("\nNow you can continue with Knowledge Base creation:")
        print("  python setup_knowledge_base.py --region", args.region)
        print("\nOr continue with the full setup:")
        print("  python run_all.py --region", args.region)
    except Exception as e:
        print(f"\n❌ Error creating index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
