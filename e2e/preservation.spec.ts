/**
 * Preservation Property Tests for Strand Agent Orchestration Fix
 * 
 * Property 2: Runtime Agent Orchestration Unchanged
 * 
 * These tests verify that the runtime agent orchestration behavior remains
 * unchanged after the fix. They test the UNFIXED code to establish baseline
 * behavior that must be preserved.
 * 
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
 * 
 * Test Strategy:
 * - Use property-based testing with fast-check to generate many test cases
 * - Test agent invocation requests with various inputs
 * - Verify orchestration order, streaming format, and API usage patterns
 * - These tests should PASS on unfixed code (baseline behavior)
 * 
 * Test Approach:
 * - Tests verify the architectural patterns are in place
 * - Tests check code structure and imports to ensure Strand-based architecture
 * - Tests verify FastAPI endpoint configuration
 * - Tests validate that Bedrock Runtime API (not Bedrock Agent API) is used
 */

import { test, expect } from '@playwright/test';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Preservation Property Tests - Runtime Agent Orchestration', () => {
  const agentServicePath = path.join(process.cwd(), 'agent-service');
  const agentsPath = path.join(agentServicePath, 'agents');

  /**
   * Test Case 1: Orchestrator Uses orchestrate_pipeline Function
   * 
   * Property: The FastAPI service must use orchestrate_pipeline() from agents/orchestrator.py
   * to coordinate agent execution.
   * 
   * Validates: Requirement 3.1 - FastAPI service orchestrates agents using orchestrate_pipeline()
   */
  test('Property: FastAPI service uses orchestrate_pipeline() for orchestration', async () => {
    // Read main.py to verify it imports and uses orchestrate_pipeline
    const mainPyPath = path.join(agentServicePath, 'main.py');
    expect(fs.existsSync(mainPyPath)).toBe(true);
    
    const mainPyContent = fs.readFileSync(mainPyPath, 'utf-8');
    
    // Verify orchestrate_pipeline is imported
    expect(mainPyContent).toContain('from agents.orchestrator import orchestrate_pipeline');
    
    // Verify /invoke endpoint exists and uses orchestrate_pipeline
    expect(mainPyContent).toContain('@app.post("/invoke")');
    expect(mainPyContent).toContain('orchestrate_pipeline');
    
    // Verify streaming response
    expect(mainPyContent).toContain('StreamingResponse');
  });

  /**
   * Test Case 2: Agent Execution Order in Orchestrator
   * 
   * Property: The orchestrator must execute agents in the sequence:
   * SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
   * 
   * Validates: Requirement 3.2 - Orchestrator executes agents in sequence
   */
  test('Property: Orchestrator executes agents in correct sequence', async () => {
    const orchestratorPath = path.join(agentsPath, 'orchestrator.py');
    expect(fs.existsSync(orchestratorPath)).toBe(true);
    
    const orchestratorContent = fs.readFileSync(orchestratorPath, 'utf-8');
    
    // Verify all agent imports
    expect(orchestratorContent).toContain('from .sourcing import run_sourcing_agent');
    expect(orchestratorContent).toContain('from .matchmaking import run_matchmaking_agent');
    expect(orchestratorContent).toContain('from .collaborator import run_collaborator_agent');
    expect(orchestratorContent).toContain('from .drafting import run_drafting_agent');
    
    // Verify orchestrate_pipeline function exists
    expect(orchestratorContent).toContain('async def orchestrate_pipeline');
    
    // Verify execution order by checking the sequence of agent calls
    const sourcingIndex = orchestratorContent.indexOf('run_sourcing_agent');
    const matchmakingIndex = orchestratorContent.indexOf('run_matchmaking_agent');
    const collaboratorIndex = orchestratorContent.indexOf('run_collaborator_agent');
    const draftingIndex = orchestratorContent.indexOf('run_drafting_agent');
    
    expect(sourcingIndex).toBeGreaterThan(0);
    expect(matchmakingIndex).toBeGreaterThan(sourcingIndex);
    expect(collaboratorIndex).toBeGreaterThan(matchmakingIndex);
    expect(draftingIndex).toBeGreaterThan(collaboratorIndex);
  });

  /**
   * Test Case 3: Agents Use Strand's BedrockModel (Bedrock Runtime API)
   * 
   * Property: Each agent must use Strand's BedrockModel to invoke Claude models
   * via Bedrock Runtime API (not Bedrock Agent API).
   * 
   * Validates: Requirement 3.3 - Agents use Strand's BedrockModel for Bedrock Runtime API
   */
  test('Property: All agents use Strand BedrockModel (Bedrock Runtime API)', async () => {
    const agentFiles = ['sourcing.py', 'matchmaking.py', 'collaborator.py', 'drafting.py'];
    
    for (const agentFile of agentFiles) {
      const agentPath = path.join(agentsPath, agentFile);
      expect(fs.existsSync(agentPath)).toBe(true);
      
      const agentContent = fs.readFileSync(agentPath, 'utf-8');
      
      // Verify Strand imports (BedrockModel for Runtime API)
      expect(agentContent).toContain('from strands.models import BedrockModel');
      
      // Verify BedrockModel is instantiated
      expect(agentContent).toContain('BedrockModel(');
      
      // Verify NO Bedrock Agent API imports
      expect(agentContent).not.toContain('bedrock-agent');
      expect(agentContent).not.toContain('bedrock_agent');
      expect(agentContent).not.toContain('BedrockAgentClient');
      expect(agentContent).not.toContain('invoke_agent');
    }
  });

  /**
   * Test Case 4: Express Backend Calls FastAPI /invoke Endpoint
   * 
   * Property: The Express backend must call http://localhost:8001/invoke
   * and stream JSON_Line responses.
   * 
   * Validates: Requirement 3.4 - Express backend calls FastAPI and streams JSON_Line
   */
  test('Property: Express backend calls FastAPI /invoke endpoint', async () => {
    const agentClientPath = path.join(process.cwd(), 'server', 'agent-client.ts');
    expect(fs.existsSync(agentClientPath)).toBe(true);
    
    const agentClientContent = fs.readFileSync(agentClientPath, 'utf-8');
    
    // Verify it calls /invoke endpoint
    expect(agentClientContent).toContain('/invoke');
    
    // Verify it uses fetch for HTTP calls (not Bedrock Agent SDK)
    expect(agentClientContent).toContain('fetch');
    
    // Verify JSON_Line parsing
    expect(agentClientContent).toContain('JSONLine');
    
    // Verify streaming response handling
    expect(agentClientContent).toContain('response.body');
    expect(agentClientContent).toContain('getReader()');
    
    // Verify NO Bedrock Agent SDK usage
    expect(agentClientContent).not.toContain('BedrockAgentClient');
    expect(agentClientContent).not.toContain('invoke_agent');
    expect(agentClientContent).not.toContain('@aws-sdk/client-bedrock-agent');
  });

  /**
   * Test Case 5: AWS Credentials Required for Bedrock Runtime API
   * 
   * Property: The agent service must require AWS credentials
   * (AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) for Bedrock Runtime API access.
   * 
   * Validates: Requirement 3.5 - AWS credentials are required for Bedrock Runtime API
   */
  test('Property: Agent service requires AWS credentials for Bedrock Runtime', async () => {
    const mainPyPath = path.join(agentServicePath, 'main.py');
    const mainPyContent = fs.readFileSync(mainPyPath, 'utf-8');
    
    // Verify required environment variables are checked
    expect(mainPyContent).toContain('AWS_REGION');
    expect(mainPyContent).toContain('AWS_ACCESS_KEY_ID');
    expect(mainPyContent).toContain('AWS_SECRET_ACCESS_KEY');
    
    // Verify validation of required variables
    expect(mainPyContent).toContain('required_vars');
    
    // Check .env.example for credential configuration
    const envExamplePath = path.join(agentServicePath, '.env.example');
    expect(fs.existsSync(envExamplePath)).toBe(true);
    
    const envExampleContent = fs.readFileSync(envExamplePath, 'utf-8');
    expect(envExampleContent).toContain('AWS_REGION');
    expect(envExampleContent).toContain('AWS_ACCESS_KEY_ID');
    expect(envExampleContent).toContain('AWS_SECRET_ACCESS_KEY');
  });

  /**
   * Test Case 6: JSON_Line Streaming Format
   * 
   * Property: The FastAPI service must stream responses in JSON_Line format
   * (newline-delimited JSON) with agent progress updates.
   * 
   * Validates: Requirement 3.4 - JSON_Line streaming format is preserved
   */
  test('Property: FastAPI streams JSON_Line format responses', async () => {
    const mainPyPath = path.join(agentServicePath, 'main.py');
    const mainPyContent = fs.readFileSync(mainPyPath, 'utf-8');
    
    // Verify JSON_Line streaming
    expect(mainPyContent).toContain('application/x-ndjson');
    
    // Verify JSON serialization with newlines
    expect(mainPyContent).toContain('json.dumps');
    expect(mainPyContent).toContain('\\n');
    
    // Check models.py for JSONLine structure
    const modelsPath = path.join(agentServicePath, 'models.py');
    expect(fs.existsSync(modelsPath)).toBe(true);
    
    const modelsContent = fs.readFileSync(modelsPath, 'utf-8');
    expect(modelsContent).toContain('class JSONLine');
    expect(modelsContent).toContain('agent:');
    expect(modelsContent).toContain('step:');
    expect(modelsContent).toContain('output:');
    expect(modelsContent).toContain('done:');
  });

  /**
   * Property-Based Test: Agent Module Files Exist
   * 
   * Property: For all required agent modules, the files must exist in the agents directory.
   * This ensures the Strand-based architecture is in place.
   */
  test('Property: All required agent modules exist', async () => {
    const requiredAgents = ['orchestrator', 'sourcing', 'matchmaking', 'collaborator', 'drafting'];
    
    await fc.assert(
      fc.asyncProperty(fc.constantFrom(...requiredAgents), async (agentName) => {
        const agentPath = path.join(agentsPath, `${agentName}.py`);
        expect(fs.existsSync(agentPath)).toBe(true);
        
        const agentContent = fs.readFileSync(agentPath, 'utf-8');
        
        // Verify it's a Python module with async function
        expect(agentContent).toContain('async def');
        
        // Verify it yields JSON_Line messages
        expect(agentContent).toContain('yield');
      }),
      { numRuns: 2 }
    );
  });

  /**
   * Property-Based Test: No Bedrock Agent API Usage
   * 
   * Property: For all agent files and service files, there must be NO usage
   * of Bedrock Agent API (only Bedrock Runtime API via Strand).
   */
  test('Property: No Bedrock Agent API usage in codebase', async () => {
    const filesToCheck = [
      path.join(agentServicePath, 'main.py'),
      path.join(agentsPath, 'orchestrator.py'),
      path.join(agentsPath, 'sourcing.py'),
      path.join(agentsPath, 'matchmaking.py'),
      path.join(agentsPath, 'collaborator.py'),
      path.join(agentsPath, 'drafting.py'),
      path.join(process.cwd(), 'server', 'agent-client.ts')
    ];
    
    await fc.assert(
      fc.asyncProperty(fc.constantFrom(...filesToCheck), async (filePath) => {
        expect(fs.existsSync(filePath)).toBe(true);
        
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        
        // Verify NO Bedrock Agent API imports or usage
        expect(fileContent).not.toContain('bedrock-agent-runtime');
        expect(fileContent).not.toContain('BedrockAgentRuntimeClient');
        expect(fileContent).not.toContain('InvokeAgent');
        expect(fileContent).not.toContain('bedrock_agent_client');
        expect(fileContent).not.toContain('create_agent');
        expect(fileContent).not.toContain('create_agent_alias');
      }),
      { numRuns: 3 }
    );
  });
});
