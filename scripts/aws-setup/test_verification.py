#!/usr/bin/env python3
"""
Test script to verify the setup_bedrock_agents.py verification functions
"""

import os
import sys
import tempfile
import shutil

# Add the script directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from setup_bedrock_agents import (
    verify_agent_modules,
    verify_aws_credentials,
    verify_dependencies,
    verify_fastapi_health
)

def test_verify_agent_modules():
    """Test agent module verification"""
    print("\n=== Testing verify_agent_modules ===")
    
    # Test with actual agent-service directory
    result = verify_agent_modules('agent-service/agents')
    print(f"Result with real directory: {result}")
    assert result == True, "Should find all agent modules"
    
    # Test with non-existent directory
    result = verify_agent_modules('non-existent-directory')
    print(f"Result with non-existent directory: {result}")
    assert result == False, "Should fail with non-existent directory"
    
    print("✓ verify_agent_modules tests passed")

def test_verify_aws_credentials():
    """Test AWS credentials verification"""
    print("\n=== Testing verify_aws_credentials ===")
    
    # Save original environment
    original_env = {
        'AWS_REGION': os.environ.get('AWS_REGION'),
        'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY')
    }
    
    try:
        # Test with all credentials set
        os.environ['AWS_REGION'] = 'us-east-1'
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'
        
        result = verify_aws_credentials()
        print(f"Result with all credentials: {result}")
        assert result == True, "Should pass with all credentials"
        
        # Test with missing AWS_REGION
        del os.environ['AWS_REGION']
        result = verify_aws_credentials()
        print(f"Result with missing AWS_REGION: {result}")
        assert result == False, "Should fail with missing AWS_REGION"
        
        print("✓ verify_aws_credentials tests passed")
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

def test_verify_dependencies():
    """Test dependencies verification"""
    print("\n=== Testing verify_dependencies ===")
    
    # Test with actual agent-service directory
    result = verify_dependencies('agent-service/agents')
    print(f"Result with real directory: {result}")
    # Should return True even if requirements.txt is not found (non-fatal warning)
    assert result == True, "Should return True (non-fatal)"
    
    print("✓ verify_dependencies tests passed")

def test_verify_fastapi_health():
    """Test FastAPI health check"""
    print("\n=== Testing verify_fastapi_health ===")
    
    # Test with service not running (expected to fail gracefully)
    result = verify_fastapi_health('http://localhost:8001')
    print(f"Result with service not running: {result}")
    # Should return False but not crash (non-fatal)
    assert result == False, "Should return False when service is not running"
    
    print("✓ verify_fastapi_health tests passed")

if __name__ == '__main__':
    print("Running verification function tests...")
    
    try:
        test_verify_agent_modules()
        test_verify_aws_credentials()
        test_verify_dependencies()
        test_verify_fastapi_health()
        
        print("\n" + "=" * 60)
        print("✓ All verification function tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
