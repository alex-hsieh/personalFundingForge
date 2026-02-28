/**
 * Bug Condition Exploration Test for Strand Agent Orchestration Fix
 * 
 * **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
 * 
 * CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
 * DO NOT attempt to fix the test or the code when it fails.
 * 
 * This test encodes the expected behavior - it will validate the fix when it passes after implementation.
 * 
 * GOAL: Surface counterexamples that demonstrate the architectural mismatch:
 * - setup_bedrock_agents.py attempts to create Bedrock agents using bedrock_client.create_agent()
 * - Script generates agent_config.json with Bedrock agent IDs that are never used by runtime
 * - ValidationException occurs when creating agent aliases before agents are fully provisioned
 * - No verification of Strand agent modules or FastAPI service configuration
 */

import { test, expect } from '@playwright/test';
import * as fc from 'fast-check';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

/**
 * Property 1: Fault Condition - Setup Script Creates Bedrock Agents
 * 
 * For any execution of the setup script where the system uses Strand-based agent orchestration,
 * the setup script should verify that the FastAPI agent service is properly configured
 * WITHOUT attempting to create Bedrock agents or agent aliases.
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3**
 */
test.describe('Bug Condition Exploration: Setup Script Architectural Mismatch', () => {
  
  test('Property 1: Setup script should NOT attempt to create Bedrock agents when Strand architecture is used', async () => {
    // This property-based test verifies the fault condition by checking:
    // 1. The setup script contains calls to bedrock_client.create_agent()
    // 2. The setup script contains calls to bedrock_client.create_agent_alias()
    // 3. The runtime uses Strand-based agents (not Bedrock agents)
    // 4. The generated config contains Bedrock agent IDs (architectural mismatch)
    
    await fc.assert(
      fc.asyncProperty(
        // Generate arbitrary agent configurations that would be created
        fc.record({
          agentNames: fc.constantFrom(
            'FundingForge-Supervisor',
            'FundingForge-Sourcing',
            'FundingForge-Matchmaking',
            'FundingForge-Collaborator',
            'FundingForge-Drafting'
          ),
          region: fc.constantFrom('us-east-1', 'us-west-2', 'eu-west-1'),
          model: fc.constant('anthropic.claude-3-5-sonnet-20241022-v2:0')
        }),
        async (config) => {
          // Read the setup script to verify it contains Bedrock agent creation logic
          const setupScriptPath = join(process.cwd(), 'scripts/aws-setup/setup_bedrock_agents.py');
          expect(existsSync(setupScriptPath)).toBe(true);
          
          const setupScriptContent = readFileSync(setupScriptPath, 'utf-8');
          
          // FAULT CONDITION CHECK 1: Script attempts to create Bedrock agents
          // Expected on UNFIXED code: This assertion PASSES (script contains create_agent calls)
          // Expected on FIXED code: This assertion FAILS (script no longer creates agents)
          const containsCreateAgent = setupScriptContent.includes('bedrock_client.create_agent(');
          const containsCreateAlias = setupScriptContent.includes('bedrock_client.create_agent_alias(');
          
          // FAULT CONDITION CHECK 2: Verify Strand-based agent modules exist
          // This confirms the runtime uses Strand architecture, not Bedrock agents
          const strandAgentModules = [
            'agent-service/agents/orchestrator.py',
            'agent-service/agents/sourcing.py',
            'agent-service/agents/matchmaking.py',
            'agent-service/agents/collaborator.py',
            'agent-service/agents/drafting.py'
          ];
          
          const strandModulesExist = strandAgentModules.every(modulePath => 
            existsSync(join(process.cwd(), modulePath))
          );
          
          // FAULT CONDITION CHECK 3: Verify agent-client.ts calls FastAPI, not Bedrock Agent API
          const agentClientPath = join(process.cwd(), 'server/agent-client.ts');
          const agentClientContent = readFileSync(agentClientPath, 'utf-8');
          const callsFastAPI = agentClientContent.includes('http://localhost:8001/invoke') ||
                               agentClientContent.includes('localhost:8001');
          const callsBedrockAgentAPI = agentClientContent.includes('bedrock-agent-runtime') ||
                                       agentClientContent.includes('invokeAgent');
          
          // ARCHITECTURAL MISMATCH ASSERTION
          // This assertion encodes the EXPECTED behavior (what should be true after the fix):
          // - Setup script should NOT create Bedrock agents (containsCreateAgent should be false)
          // - Setup script should NOT create agent aliases (containsCreateAlias should be false)
          // - Strand agent modules SHOULD exist (strandModulesExist should be true)
          // - Runtime SHOULD call FastAPI (callsFastAPI should be true)
          // - Runtime should NOT call Bedrock Agent API (callsBedrockAgentAPI should be false)
          //
          // ON UNFIXED CODE: This will FAIL because:
          // - containsCreateAgent = true (script creates agents)
          // - containsCreateAlias = true (script creates aliases)
          // - This proves the bug exists
          //
          // ON FIXED CODE: This will PASS because:
          // - containsCreateAgent = false (script no longer creates agents)
          // - containsCreateAlias = false (script no longer creates aliases)
          // - This proves the fix works
          expect(containsCreateAgent).toBe(false); // Should NOT create Bedrock agents
          expect(containsCreateAlias).toBe(false); // Should NOT create agent aliases
          expect(strandModulesExist).toBe(true);   // Strand modules should exist
          expect(callsFastAPI).toBe(true);         // Runtime should use FastAPI
          expect(callsBedrockAgentAPI).toBe(false); // Runtime should NOT use Bedrock Agent API
        }
      ),
      { numRuns: 3 } // Run 3 times with different agent configurations
    );
  });

  test('Property 1.1: Setup script generates config with Bedrock agent IDs (architectural mismatch)', async () => {
    // This test verifies that the setup script generates agent_config.json with Bedrock agent IDs
    // that are never used by the runtime system (architectural mismatch)
    
    const setupScriptPath = join(process.cwd(), 'scripts/aws-setup/setup_bedrock_agents.py');
    const setupScriptContent = readFileSync(setupScriptPath, 'utf-8');
    
    // Check if script generates config with agent IDs
    const generatesAgentConfig = setupScriptContent.includes("'agents': {}") ||
                                  setupScriptContent.includes('"agents": {}');
    const savesAgentIds = setupScriptContent.includes("'id': agent_id") ||
                          setupScriptContent.includes('"id": agent_id');
    
    // Check if runtime actually uses agent_config.json
    const agentClientPath = join(process.cwd(), 'server/agent-client.ts');
    const agentClientContent = readFileSync(agentClientPath, 'utf-8');
    const readsAgentConfig = agentClientContent.includes('agent_config.json');
    
    // EXPECTED BEHAVIOR (after fix):
    // - Script should NOT generate config with Bedrock agent IDs
    // - Script should generate config with FastAPI service endpoint instead
    //
    // ON UNFIXED CODE: This will FAIL because:
    // - generatesAgentConfig = true (script generates agent config)
    // - savesAgentIds = true (script saves Bedrock agent IDs)
    // - readsAgentConfig = false (runtime never reads the config)
    // - This proves the architectural mismatch
    //
    // ON FIXED CODE: This will PASS because:
    // - Script generates Strand service configuration instead
    expect(savesAgentIds).toBe(false); // Should NOT save Bedrock agent IDs
    expect(readsAgentConfig || !generatesAgentConfig).toBe(true); // Config should be used OR not generated
  });

  test('Property 1.2: Setup script contains timing issue with agent alias creation', async () => {
    // This test verifies that the setup script attempts to create agent aliases
    // immediately after agent creation, which causes ValidationException
    
    const setupScriptPath = join(process.cwd(), 'scripts/aws-setup/setup_bedrock_agents.py');
    const setupScriptContent = readFileSync(setupScriptPath, 'utf-8');
    
    // Check for the problematic pattern: create_agent followed by create_agent_alias
    // without proper waiting for agent to reach stable state
    const hasCreateAgentFunction = setupScriptContent.includes('def create_bedrock_agent(');
    const createsAgentAlias = setupScriptContent.includes('create_agent_alias(');
    
    // Check if there's proper waiting logic (looking for agent status checks)
    const hasProperWaiting = setupScriptContent.includes("status in ['NOT_PREPARED', 'PREPARED', 'FAILED']");
    
    // EXPECTED BEHAVIOR (after fix):
    // - Script should NOT create agent aliases at all (since it shouldn't create agents)
    //
    // ON UNFIXED CODE: This will FAIL because:
    // - hasCreateAgentFunction = true
    // - createsAgentAlias = true
    // - Even with waiting logic, timing issues can occur
    // - This proves the ValidationException bug exists
    //
    // ON FIXED CODE: This will PASS because:
    // - createsAgentAlias = false (no alias creation)
    expect(createsAgentAlias).toBe(false); // Should NOT create agent aliases
  });

  test('Property 1.3: Runtime uses Strand orchestration, not Bedrock agents', async () => {
    // This test verifies that the runtime architecture uses Strand-based agents
    // orchestrated through FastAPI, not Bedrock agents
    
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          endpoint: fc.constant('/invoke'),
          serviceUrl: fc.constant('http://localhost:8001')
        }),
        async (config) => {
          // Verify agent-client.ts calls FastAPI service
          const agentClientPath = join(process.cwd(), 'server/agent-client.ts');
          const agentClientContent = readFileSync(agentClientPath, 'utf-8');
          
          const usesFastAPI = agentClientContent.includes(config.serviceUrl) ||
                              agentClientContent.includes('localhost:8001');
          
          // Verify FastAPI service exists and uses orchestrator
          const fastAPIMainPath = join(process.cwd(), 'agent-service/main.py');
          const fastAPIExists = existsSync(fastAPIMainPath);
          
          let usesOrchestrator = false;
          if (fastAPIExists) {
            const fastAPIContent = readFileSync(fastAPIMainPath, 'utf-8');
            usesOrchestrator = fastAPIContent.includes('orchestrate_pipeline') ||
                               fastAPIContent.includes('from agents.orchestrator');
          }
          
          // Verify Strand agent modules exist
          const orchestratorPath = join(process.cwd(), 'agent-service/agents/orchestrator.py');
          const orchestratorExists = existsSync(orchestratorPath);
          
          let usesStrandBedrockModel = false;
          if (orchestratorExists) {
            const orchestratorContent = readFileSync(orchestratorPath, 'utf-8');
            usesStrandBedrockModel = orchestratorContent.includes('BedrockModel') ||
                                     orchestratorContent.includes('from strand');
          }
          
          // EXPECTED BEHAVIOR:
          // - Runtime SHOULD use FastAPI service
          // - FastAPI SHOULD use orchestrator
          // - Orchestrator SHOULD use Strand's BedrockModel
          // - This confirms the runtime uses Strand architecture, not Bedrock agents
          //
          // This assertion should PASS on both unfixed and fixed code
          // because the runtime architecture is already correct.
          // The bug is in the setup script, not the runtime.
          expect(usesFastAPI).toBe(true);
          expect(fastAPIExists).toBe(true);
          expect(usesOrchestrator).toBe(true);
          expect(orchestratorExists).toBe(true);
          expect(usesStrandBedrockModel).toBe(true);
        }
      ),
      { numRuns: 2 }
    );
  });

  test('Property 1.4: Setup script requires IAM roles for Bedrock agents (unnecessary dependency)', async () => {
    // This test verifies that the setup script requires iam_config.json with IAM roles
    // for Bedrock agents, which is unnecessary for Strand architecture
    
    const setupScriptPath = join(process.cwd(), 'scripts/aws-setup/setup_bedrock_agents.py');
    const setupScriptContent = readFileSync(setupScriptPath, 'utf-8');
    
    // Check if script requires iam_config.json
    const requiresIAMConfig = setupScriptContent.includes('iam_config.json');
    const usesIAMRoles = setupScriptContent.includes("iam_config['roles']");
    
    // EXPECTED BEHAVIOR (after fix):
    // - Script should NOT require IAM roles for Bedrock agents
    // - Script should only verify AWS credentials for Bedrock Runtime API access
    //
    // ON UNFIXED CODE: This will FAIL because:
    // - requiresIAMConfig = true (script requires IAM config)
    // - usesIAMRoles = true (script uses IAM roles for agent creation)
    // - This proves the unnecessary dependency
    //
    // ON FIXED CODE: This will PASS because:
    // - Script no longer requires IAM roles for Bedrock agents
    expect(usesIAMRoles).toBe(false); // Should NOT use IAM roles for Bedrock agents
  });
});
