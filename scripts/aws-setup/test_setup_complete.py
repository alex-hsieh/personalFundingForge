#!/usr/bin/env python3
"""
Test the complete setup script with all environment variables set
"""

import os
import sys
import json
import subprocess

# Set required environment variables
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test-key-id'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret-key'

print("Running setup_bedrock_agents.py with all environment variables set...")
print()

# Run the setup script
result = subprocess.run(
    [sys.executable, 'scripts/aws-setup/setup_bedrock_agents.py', '--agent-service-path', 'agent-service/agents'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

if result.returncode != 0:
    print(f"\n❌ Setup script failed with exit code {result.returncode}")
    sys.exit(1)

# Verify the generated configuration
print("\n=== Verifying generated configuration ===")
try:
    with open('agent_config.json', 'r') as f:
        config = json.load(f)
    
    print("Generated configuration:")
    print(json.dumps(config, indent=2))
    
    # Verify expected fields
    assert config['architecture'] == 'strand-fastapi', "Architecture should be 'strand-fastapi'"
    assert config['agentServiceUrl'] == 'http://localhost:8001', "Service URL should be 'http://localhost:8001'"
    assert config['agentServiceEndpoint'] == '/invoke', "Endpoint should be '/invoke'"
    assert len(config['requiredAgents']) == 5, "Should have 5 required agents"
    assert 'orchestrator' in config['requiredAgents'], "Should include orchestrator"
    assert 'sourcing' in config['requiredAgents'], "Should include sourcing"
    assert 'matchmaking' in config['requiredAgents'], "Should include matchmaking"
    assert 'collaborator' in config['requiredAgents'], "Should include collaborator"
    assert 'drafting' in config['requiredAgents'], "Should include drafting"
    assert config['bedrockRuntimeConfig']['region'] == 'us-east-1', "Region should be 'us-east-1'"
    assert 'model' in config['bedrockRuntimeConfig'], "Should have model configuration"
    
    print("\n✓ Configuration is correct!")
    print("\n=== All tests passed! ===")
    
except FileNotFoundError:
    print("❌ agent_config.json was not generated")
    sys.exit(1)
except AssertionError as e:
    print(f"❌ Configuration validation failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
