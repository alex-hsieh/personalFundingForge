# Bugfix Requirements Document

## Introduction

The FundingForge application has an architectural mismatch where the AWS setup script (`setup_bedrock_agents.py`) attempts to create agents directly in AWS Bedrock, but the actual runtime architecture uses Strand-based Python agents orchestrated through a FastAPI service. This causes ValidationException errors when trying to create agent aliases before agents are fully provisioned in Bedrock.

The bug manifests as: "Create operation can't be performed on AgentAlias when Agent is in Creating state. Retry your request after the Agent is created"

The fix involves removing the Bedrock agent creation logic and ensuring the setup process aligns with the existing Strand-based architecture where agents are Python modules (`orchestrator.py`, `collaborator.py`, `drafting.py`, `matchmaking.py`, `sourcing.py`) invoked via FastAPI HTTP endpoints.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `setup_bedrock_agents.py` is executed THEN the system attempts to create agents directly in AWS Bedrock using `bedrock_client.create_agent()`

1.2 WHEN the script tries to create agent aliases immediately after agent creation THEN the system throws ValidationException: "Create operation can't be performed on AgentAlias when Agent is in Creating state"

1.3 WHEN the setup script completes THEN it generates `agent_config.json` with Bedrock agent IDs that are never used by the runtime system

1.4 WHEN the Express backend invokes agents THEN it calls the FastAPI service at `http://localhost:8001/invoke`, completely bypassing any Bedrock agents

### Expected Behavior (Correct)

2.1 WHEN `setup_bedrock_agents.py` is executed THEN the system SHALL verify that the Strand-based agent service is properly configured without attempting to create Bedrock agents

2.2 WHEN the setup process runs THEN the system SHALL NOT attempt to create agent aliases in AWS Bedrock

2.3 WHEN the setup script completes THEN it SHALL generate configuration that references the FastAPI agent service endpoint, not Bedrock agent IDs

2.4 WHEN the Express backend invokes agents THEN it SHALL continue to call the FastAPI service which orchestrates the Strand-based Python agents

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the FastAPI service receives an `/invoke` request THEN the system SHALL CONTINUE TO orchestrate agents using `orchestrate_pipeline()` from `agents/orchestrator.py`

3.2 WHEN the orchestrator runs THEN the system SHALL CONTINUE TO execute agents in sequence: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent

3.3 WHEN each agent executes THEN the system SHALL CONTINUE TO use Strand's BedrockModel to invoke Claude models for AI processing

3.4 WHEN the agent-client.ts invokes the pipeline THEN the system SHALL CONTINUE TO stream JSON_Line responses from the FastAPI service

3.5 WHEN agents use Bedrock models THEN the system SHALL CONTINUE TO require AWS credentials (AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) for model invocation
