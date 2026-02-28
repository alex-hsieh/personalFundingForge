#!/usr/bin/env python3
"""
Master Script - Run All AWS Setup Scripts

Executes all setup scripts in the correct order:
1. IAM Roles
2. Knowledge Base (optional)
3. Lambda Functions
4. Bedrock Agents
5. Link Action Groups
6. Generate .env file
"""

import subprocess
import argparse
import sys
import time

def run_script(script_name: str, region: str, extra_args: list = None) -> bool:
    """Run a Python script and return success status"""
    print("\n" + "=" * 60)
    print(f"Running: {script_name}")
    print("=" * 60)
    print()
    
    cmd = ['python', script_name, '--region', region]
    if extra_args:
        cmd.extend(extra_args)
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Error: {script_name} not found")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run all AWS setup scripts')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--skip-kb', action='store_true', help='Skip Knowledge Base setup')
    parser.add_argument('--skip-sample-docs', action='store_true', help='Skip uploading sample documents')
    args = parser.parse_args()
    
    print("=" * 60)
    print("FundingForge - Complete AWS Infrastructure Setup")
    print("=" * 60)
    print()
    print(f"Region: {args.region}")
    print(f"Skip Knowledge Base: {args.skip_kb}")
    print(f"Skip Sample Docs: {args.skip_sample_docs}")
    print()
    print("This will create:")
    print("  • IAM roles for all agents and Lambda functions")
    if not args.skip_kb:
        print("  • S3 bucket and OpenSearch Serverless collection")
        print("  • Bedrock Knowledge Base with sample documents")
    print("  • 3 Lambda Action Groups")
    print("  • 5 Bedrock Agents (Supervisor + 4 Sub-Agents)")
    print("  • Action Group linkages")
    print("  • Environment configuration file")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    start_time = time.time()
    
    # Step 1: IAM Roles
    if not run_script('setup_iam_roles.py', args.region):
        print("\n❌ Failed at step 1: IAM Roles")
        sys.exit(1)
    
    # Step 2: Knowledge Base (optional)
    if not args.skip_kb:
        kb_args = ['--skip-sample-docs'] if args.skip_sample_docs else []
        if not run_script('setup_knowledge_base.py', args.region, kb_args):
            print("\n❌ Failed at step 2: Knowledge Base")
            print("You can skip this step with --skip-kb flag")
            sys.exit(1)
    else:
        print("\n⚠️  Skipping Knowledge Base setup")
    
    # Step 3: Lambda Functions
    if not run_script('deploy_lambda_functions.py', args.region):
        print("\n❌ Failed at step 3: Lambda Functions")
        sys.exit(1)
    
    # Step 4: Bedrock Agents
    if not run_script('setup_bedrock_agents.py', args.region):
        print("\n❌ Failed at step 4: Bedrock Agents")
        sys.exit(1)
    
    # Step 5: Link Action Groups
    if not run_script('link_action_groups.py', args.region):
        print("\n❌ Failed at step 5: Link Action Groups")
        sys.exit(1)
    
    # Step 6: Generate .env file
    if not run_script('generate_env_file.py', args.region):
        print("\n❌ Failed at step 6: Generate .env file")
        sys.exit(1)
    
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("\n" + "=" * 60)
    print("✓ COMPLETE AWS INFRASTRUCTURE SETUP SUCCESSFUL!")
    print("=" * 60)
    print(f"\nTotal time: {minutes}m {seconds}s")
    print()
    print("Generated files:")
    print("  • iam_config.json")
    if not args.skip_kb:
        print("  • knowledge_base_config.json")
    print("  • lambda_config.json")
    print("  • agent_config.json")
    print("  • action_groups_config.json")
    print("  • .env.aws")
    print()
    print("Next steps:")
    print("  1. Review .env.aws and add your AWS credentials")
    print("  2. Copy to project root: cat .env.aws >> ../../.env")
    print("  3. Test the Supervisor Agent via AWS Console")
    print("  4. Start Developer B tasks (Express backend refactoring)")
    print()
    print("To test the Supervisor Agent:")
    print("  aws bedrock-agent-runtime invoke-agent \\")
    print("    --agent-id <SUPERVISOR_AGENT_ID> \\")
    print("    --agent-alias-id <ALIAS_ID> \\")
    print("    --session-id test-session \\")
    print("    --input-text 'Test invocation'")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
