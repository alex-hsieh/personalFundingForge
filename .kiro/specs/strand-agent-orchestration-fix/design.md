# Strand Agent Orchestration Fix - Bugfix Design

## Overview

The FundingForge application has an architectural mismatch where the AWS setup script (`setup_bedrock_agents.py`) attempts to create agents directly in AWS Bedrock using the Bedrock Agent API, but the actual runtime architecture uses Strand-based Python agents orchestrated through a FastAPI service. This causes ValidationException errors when the setup script tries to create agent aliases before agents are fully provisioned in Bedrock.

The fix involves removing all Bedrock agent creation logic from the setup script and aligning it with the existing Strand-based architecture where agents are Python modules (`orchestrator.py`, `collaborator.py`, `drafting.py`, `matchmaking.py`, `sourcing.py`) that use Strand's BedrockModel to invoke Claude models directly via the Bedrock Runtime API (not the Bedrock Agent API).

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `setup_bedrock_agents.py` is executed and attempts to create Bedrock agents
- **Property (P)**: The desired behavior - setup script should verify Strand agent configuration without creating Bedrock agents
- **Preservation**: Existing Strand-based agent orchestration via FastAPI that must remain unchanged by the fix
- **Bedrock Agent API**: AWS service for creating managed multi-agent systems (not used in our architecture)
- **Bedrock Runtime API**: AWS service for invoking foundation models directly (used by Strand's BedrockModel)
- **Strand**: Python framework for building agentic workflows that uses Bedrock Runtime API for model invocation
- **orchestrate_pipeline()**: The function in `agent-service/agents/orchestrator.py` that coordinates agent execution
- **FastAPI /invoke endpoint**: The HTTP endpoint at `http://localhost:8001/invoke` that the Express backend calls
- **JSON_Line**: Newline-delimited JSON streaming format used for agent progress updates

## Bug Details

### Fault Condition

The bug manifests when a developer runs the AWS setup script to configure the FundingForge environment. The `setup_bedrock_agents.py` script attempts to create agents using the Bedrock Agent API (`bedrock_client.create_agent()`), but the runtime system never uses these Bedrock agents. Instead, the runtime uses Strand-based Python agents that directly invoke Claude models via the Bedrock Runtime API.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ScriptExecution
  OUTPUT: boolean
  
  RETURN input.scriptName == "setup_bedrock_agents.py"
         AND input.executionPath CONTAINS "create_bedrock_agent()"
         AND input.attemptedOperation IN ["create_agent", "create_agent_alias"]
         AND runtimeArchitecture == "Strand-based FastAPI"
END FUNCTION
```

### Examples

- **Example 1**: Developer runs `python setup_bedrock_agents.py` → Script calls `bedrock_client.create_agent()` for "FundingForge-Supervisor" → Agent creation succeeds but enters "Creating" state → Script immediately calls `create_agent_alias()` → ValidationException: "Create operation can't be performed on AgentAlias when Agent is in Creating state"

- **Example 2**: Developer runs setup script → Script creates 5 Bedrock agents with IDs → Script saves `agent_config.json` with Bedrock agent IDs → Express backend starts and calls `http://localhost:8001/invoke` → FastAPI service executes `orchestrate_pipeline()` → Strand agents invoke Claude models directly via Bedrock Runtime API → Bedrock agents created by setup script are never used

- **Example 3**: Developer examines `agent-client.ts` → Sees `fetch('http://localhost:8001/invoke')` → Realizes backend never calls Bedrock Agent API → Checks `orchestrator.py` → Sees Strand agents using `BedrockModel` for direct model invocation → Confirms architectural mismatch

- **Edge Case**: Developer runs setup script with `--wait` flag to wait for agent provisioning → Script successfully creates agents and aliases → `agent_config.json` contains valid Bedrock agent IDs → Runtime still ignores these IDs and uses Strand orchestration → Setup creates unused AWS resources

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- FastAPI service must continue to orchestrate agents using `orchestrate_pipeline()` from `agents/orchestrator.py`
- Orchestrator must continue to execute agents in sequence: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
- Each agent must continue to use Strand's BedrockModel to invoke Claude models via Bedrock Runtime API
- Express backend must continue to call `http://localhost:8001/invoke` and stream JSON_Line responses
- Agents must continue to require AWS credentials (AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) for Bedrock Runtime API access

**Scope:**
All runtime agent execution behavior should be completely unaffected by this fix. This includes:
- Agent orchestration logic in `orchestrator.py`
- Individual agent implementations (sourcing.py, matchmaking.py, collaborator.py, drafting.py)
- FastAPI endpoint behavior and JSON_Line streaming
- Express backend integration via `agent-client.ts`
- AWS credential configuration for Bedrock Runtime API access

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Architectural Misunderstanding**: The setup script was written assuming a Bedrock Agent-based architecture (managed multi-agent system), but the runtime was implemented using Strand (direct model invocation framework). These are two completely different AWS Bedrock service APIs:
   - Bedrock Agent API: Creates managed agents with action groups, knowledge bases, and orchestration
   - Bedrock Runtime API: Directly invokes foundation models (used by Strand's BedrockModel)

2. **Configuration Mismatch**: The setup script generates `agent_config.json` with Bedrock agent IDs and ARNs, but the runtime code never reads or uses this configuration. The Express backend is hardcoded to call `http://localhost:8001/invoke`, and the FastAPI service directly imports and executes Python agent modules.

3. **Timing Issue in Agent Provisioning**: Even if the architecture were correct, the script attempts to create agent aliases immediately after agent creation without properly waiting for agents to reach a stable state. Bedrock agents go through states: Creating → Not Prepared → Prepared, and aliases can only be created when agents are in a stable state.

4. **Missing Runtime Integration**: There is no code path in the runtime that would use Bedrock agents even if they were successfully created. The `agent-client.ts` makes direct HTTP calls to FastAPI, and the FastAPI service imports Python modules directly - there's no Bedrock Agent SDK integration anywhere in the runtime.

## Correctness Properties

Property 1: Fault Condition - Setup Script Aligns with Strand Architecture

_For any_ execution of the setup script where the system uses Strand-based agent orchestration, the fixed setup script SHALL verify that the FastAPI agent service is properly configured and that AWS credentials for Bedrock Runtime API access are available, WITHOUT attempting to create Bedrock agents or agent aliases.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Runtime Agent Orchestration Unchanged

_For any_ agent invocation request sent to the FastAPI service, the fixed system SHALL produce exactly the same orchestration behavior as the original system, preserving the Strand-based execution flow (SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent) and direct Bedrock Runtime API model invocation.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `scripts/aws-setup/setup_bedrock_agents.py`

**Function**: `main()` and `create_bedrock_agent()`

**Specific Changes**:

1. **Remove Bedrock Agent Creation Logic**: Delete the `create_bedrock_agent()` function entirely, as it creates agents using the Bedrock Agent API which are never used by the runtime

2. **Remove Agent Provisioning Calls**: Remove all calls to:
   - `bedrock_client.create_agent()`
   - `bedrock_client.create_agent_alias()`
   - `bedrock_client.prepare_agent()`
   - `bedrock_client.get_agent()` (status polling)
   - `bedrock_client.list_agents()` (existing agent lookup)

3. **Replace with Configuration Verification**: Add verification logic to check:
   - FastAPI agent service directory exists (`agent-service/agents/`)
   - Required agent modules are present (orchestrator.py, sourcing.py, matchmaking.py, collaborator.py, drafting.py)
   - AWS credentials are configured for Bedrock Runtime API access
   - Agent service dependencies are installed (requirements.txt)

4. **Update Configuration Output**: Modify `agent_config.json` generation to output:
   ```json
   {
     "architecture": "strand-fastapi",
     "agentServiceUrl": "http://localhost:8001",
     "agentServiceEndpoint": "/invoke",
     "requiredAgents": [
       "orchestrator",
       "sourcing",
       "matchmaking",
       "collaborator",
       "drafting"
     ],
     "bedrockRuntimeConfig": {
       "region": "us-east-1",
       "model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
     }
   }
   ```

5. **Add Service Health Check**: Add a verification step that attempts to call the FastAPI `/health` endpoint to confirm the service is accessible (optional, for development convenience)

6. **Update Script Documentation**: Modify the script's docstring and print statements to reflect that it verifies Strand agent configuration rather than creating Bedrock agents

7. **Remove IAM Role Dependency**: Remove the requirement for `iam_config.json` since Strand agents don't need Bedrock Agent service roles - they only need AWS credentials for Bedrock Runtime API access

**File**: `scripts/aws-setup/agent_config.json` (generated output)

**Changes**: Replace Bedrock agent ID structure with Strand service configuration as shown above

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (ValidationException errors), then verify the fix works correctly (no agent creation, proper verification) and preserves existing runtime behavior (Strand orchestration continues working).

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the setup script attempts to create Bedrock agents and fails with ValidationException. Verify that the runtime never uses any Bedrock agents.

**Test Plan**: Run the UNFIXED `setup_bedrock_agents.py` script and observe the ValidationException when creating agent aliases. Trace the runtime execution to confirm that `agent-client.ts` calls FastAPI, not Bedrock Agent API. Verify that no code reads `agent_config.json` in the runtime.

**Test Cases**:
1. **Setup Script Execution Test**: Run `python setup_bedrock_agents.py` on unfixed code → Observe ValidationException: "Create operation can't be performed on AgentAlias when Agent is in Creating state" (will fail on unfixed code)

2. **Runtime Architecture Trace**: Start FastAPI service and Express backend → Send agent invocation request → Trace execution path → Confirm it goes through `agent-client.ts` → `fetch('http://localhost:8001/invoke')` → `orchestrate_pipeline()` → Strand agents → Bedrock Runtime API (not Bedrock Agent API)

3. **Configuration Usage Test**: Search codebase for references to `agent_config.json` → Confirm only `setup_bedrock_agents.py` writes it → Confirm no runtime code reads it (will demonstrate unused configuration on unfixed code)

4. **Agent ID Usage Test**: Search codebase for Bedrock agent ID usage → Confirm no code uses agent IDs from configuration → Confirm `agent-client.ts` uses hardcoded FastAPI URL instead (will demonstrate architectural mismatch on unfixed code)

**Expected Counterexamples**:
- ValidationException when creating agent aliases due to timing issues
- Possible causes: immediate alias creation after agent creation, insufficient wait time, agent provisioning delays
- Architectural mismatch: setup creates Bedrock agents, runtime uses Strand agents
- Unused configuration: `agent_config.json` is generated but never consumed

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (setup script execution), the fixed function produces the expected behavior (verification without agent creation).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := setup_bedrock_agents_fixed()
  ASSERT result.agentCreationAttempted == False
  ASSERT result.configurationGenerated == True
  ASSERT result.configFormat == "strand-fastapi"
  ASSERT result.verificationPerformed == True
  ASSERT result.noValidationException == True
END FOR
```

**Test Plan**: Run the FIXED setup script and verify it completes without errors, generates correct configuration, and does not attempt to create Bedrock agents.

**Test Cases**:
1. **No Agent Creation**: Run fixed setup script → Verify no calls to `bedrock_client.create_agent()` → Verify no ValidationException occurs
2. **Configuration Format**: Run fixed setup script → Verify `agent_config.json` contains Strand service configuration (not Bedrock agent IDs)
3. **Verification Logic**: Run fixed setup script → Verify it checks for agent module files → Verify it checks for AWS credentials
4. **Script Completion**: Run fixed setup script → Verify it completes successfully with appropriate success messages

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (runtime agent invocations), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT orchestrate_pipeline_original(input) = orchestrate_pipeline_fixed(input)
  ASSERT agentExecution_original(input) = agentExecution_fixed(input)
  ASSERT bedrockRuntimeCalls_original(input) = bedrockRuntimeCalls_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (different grant requests, user profiles, faculty lists)
- It catches edge cases that manual unit tests might miss (empty faculty lists, missing profile fields, long grant criteria)
- It provides strong guarantees that behavior is unchanged for all agent invocation scenarios

**Test Plan**: Observe behavior on UNFIXED code first for agent invocations, then write property-based tests capturing that behavior. Verify the FIXED code produces identical results.

**Test Cases**:
1. **Agent Orchestration Preservation**: Send agent invocation request to unfixed system → Capture JSON_Line stream output → Send same request to fixed system → Verify identical JSON_Line stream output

2. **Agent Execution Order Preservation**: Invoke pipeline on unfixed system → Verify execution order: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent → Invoke on fixed system → Verify same execution order

3. **Bedrock Runtime API Preservation**: Monitor AWS API calls during unfixed system execution → Verify calls to Bedrock Runtime API (InvokeModel) → Monitor fixed system → Verify identical API call patterns

4. **FastAPI Endpoint Preservation**: Call `/invoke` endpoint on unfixed system → Verify response format and streaming behavior → Call on fixed system → Verify identical behavior

5. **AWS Credentials Preservation**: Verify unfixed system requires AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY → Verify fixed system has same requirements

### Unit Tests

- Test setup script verification logic (checks for agent module files)
- Test configuration generation (correct JSON format for Strand architecture)
- Test AWS credential validation (environment variables present)
- Test error handling (missing agent modules, missing credentials)

### Property-Based Tests

- Generate random grant invocation requests and verify identical orchestration behavior before and after fix
- Generate random user profiles and verify identical agent execution results
- Generate random faculty lists and verify identical collaborator selection
- Test that all agent invocations continue to work across many scenarios with different input combinations

### Integration Tests

- Test full setup script execution flow (verification → configuration generation → success message)
- Test full agent invocation flow (Express → FastAPI → Orchestrator → Agents → Bedrock Runtime)
- Test that setup script changes do not affect runtime behavior
- Test that configuration file format is correct and contains expected Strand service information
