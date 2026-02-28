# Requirements Document

## Introduction

This feature upgrades the FundingForge backend to integrate a real multi-agent AI pipeline powered by AWS Strands Agents SDK (Python). The system replaces hardcoded mock steps with a FastAPI microservice that orchestrates five specialized agents (SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent, OrchestratorAgent) using AWS Bedrock models. The Express backend connects to the agent service through AWS AgentCore and proxies streaming results via Server-Sent Events (SSE) while preserving all existing API contracts to ensure zero frontend changes. The full stack runs locally for development.

## Glossary

- **Agent_Service**: Python FastAPI microservice that runs the multi-agent pipeline
- **Express_Backend**: Existing Express/TypeScript server with REST and SSE endpoints
- **Forge_Endpoint**: The /api/forge/:grantId SSE endpoint that streams proposal generation
- **SourcingAgent**: Haiku-powered agent that sources and structures data from user CV and profile
- **MatchmakingAgent**: Haiku-powered agent that analyzes user profile against grant criteria AND checks policy/compliance (FSU policies, RAMP, COI, IRB)
- **CollaboratorAgent**: Haiku-powered agent that matches faculty based on expertise
- **DraftingAgent**: Sonnet-powered agent that generates proposal narrative scaffold (highest quality output)
- **OrchestratorAgent**: Agent that coordinates execution of all four specialized agents in sequence
- **AWS_AgentCore**: AWS service that manages agent lifecycle and communication between Express backend and agent service
- **Strands_Agents**: AWS Strands Agents SDK tool for building and orchestrating AI agents
- **JSON_Line**: Single line of JSON output from agent service representing one step
- **Result_Payload**: Final complete output containing proposalDraft, collaborators, matchScore, matchJustification, and complianceChecklist
- **BedrockModel**: Strands SDK model wrapper for AWS Bedrock foundation models
- **Compliance_Checklist**: List of policy/compliance tasks with categories (RAMP, COI, IRB, Policy) and status indicators (green, yellow, red)

## Requirements

### Requirement 1: Python Agent Service Infrastructure

**User Story:** As a backend engineer, I want a dedicated Python microservice for agent orchestration, so that AI logic is decoupled from the Express server.

#### Acceptance Criteria

1. THE Agent_Service SHALL be implemented using FastAPI framework
2. THE Agent_Service SHALL expose a single endpoint: POST /invoke
3. THE Agent_Service SHALL accept JSON request body with fields: grantId, grantName, matchCriteria, eligibility, userProfile
4. THE Agent_Service SHALL run on port 8001 using uvicorn
5. THE Agent_Service SHALL be located in /agent-service/ directory
6. THE Agent_Service SHALL include a Dockerfile for containerization
7. WHEN AGENT_SERVICE_URL environment variable is set, THE Express_Backend SHALL use that URL for agent invocation
8. IF Agent_Service is unreachable, THEN THE Express_Backend SHALL fall back to mock steps with console.warn

### Requirement 2: SourcingAgent Implementation

**User Story:** As a grant applicant, I want the system to extract and structure my relevant experience and expertise from my CV and profile, so that downstream agents have accurate user data.

#### Acceptance Criteria

1. THE SourcingAgent SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0"
2. WHEN invoked, THE SourcingAgent SHALL extract relevant experience from user profile
3. WHEN invoked, THE SourcingAgent SHALL extract publications from user CV
4. WHEN invoked, THE SourcingAgent SHALL extract expertise areas from user profile
5. THE SourcingAgent SHALL return structured user data for downstream agents
6. THE SourcingAgent SHALL stream progress as JSON_Line with fields: agent, step, output, done
7. WHEN processing completes, THE SourcingAgent SHALL set done=true in final JSON_Line

### Requirement 3: MatchmakingAgent Implementation

**User Story:** As a grant applicant, I want the system to analyze how well I match the grant criteria AND check all policy/compliance requirements, so that I understand both my eligibility strength and compliance status.

#### Acceptance Criteria

1. THE MatchmakingAgent SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0"
2. WHEN invoked, THE MatchmakingAgent SHALL analyze userProfile against grant matchCriteria
3. WHEN invoked, THE MatchmakingAgent SHALL check FSU policy compliance
4. WHEN invoked, THE MatchmakingAgent SHALL check RAMP requirements
5. WHEN invoked, THE MatchmakingAgent SHALL identify COI (Conflict of Interest) triggers
6. WHEN invoked, THE MatchmakingAgent SHALL identify IRB checkpoints
7. THE MatchmakingAgent SHALL return a match score between 0 and 100 percent
8. THE MatchmakingAgent SHALL return a justification string explaining the match score
9. THE MatchmakingAgent SHALL return a Compliance_Checklist with task, category, and status for each item
10. THE MatchmakingAgent SHALL stream progress as JSON_Line with fields: agent, step, output, done
11. WHEN processing completes, THE MatchmakingAgent SHALL set done=true in final JSON_Line

### Requirement 4: DraftingAgent Implementation

**User Story:** As a grant applicant, I want the system to generate a high-quality proposal narrative scaffold, so that I have a strong starting point for my application.

#### Acceptance Criteria

1. THE DraftingAgent SHALL use BedrockModel with model_id "anthropic.claude-sonnet-4-6"
2. WHEN invoked, THE DraftingAgent SHALL use grant context and match justification
3. THE DraftingAgent SHALL generate a proposal narrative between 300 and 500 words
4. THE DraftingAgent SHALL include labeled section headers in the narrative
5. THE DraftingAgent SHALL stream progress as JSON_Line with fields: agent, step, output, done
6. WHEN processing completes, THE DraftingAgent SHALL set done=true in final JSON_Line
7. THE DraftingAgent SHALL produce the highest-quality output among all agents

### Requirement 5: CollaboratorAgent Implementation

**User Story:** As a grant applicant, I want the system to recommend relevant faculty collaborators, so that I can strengthen my proposal with appropriate expertise.

#### Acceptance Criteria

1. THE CollaboratorAgent SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0"
2. WHEN invoked, THE CollaboratorAgent SHALL receive the full faculty list from database
3. THE CollaboratorAgent SHALL match faculty based on program and expertise keywords
4. THE CollaboratorAgent SHALL return top 3 faculty members
5. THE CollaboratorAgent SHALL include relevance scores for each faculty member
6. THE CollaboratorAgent SHALL stream progress as JSON_Line with fields: agent, step, output, done
7. WHEN processing completes, THE CollaboratorAgent SHALL set done=true in final JSON_Line

### Requirement 6: OrchestratorAgent Implementation

**User Story:** As a backend engineer, I want a dedicated orchestrator agent to coordinate all specialized agents, so that the pipeline executes reliably with proper data flow.

#### Acceptance Criteria

1. THE OrchestratorAgent SHALL coordinate execution of all four specialized agents
2. THE OrchestratorAgent SHALL execute agents in order: SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent
3. WHEN each agent completes, THE OrchestratorAgent SHALL pass relevant outputs to subsequent agents
4. THE OrchestratorAgent SHALL manage data flow between agents
5. THE OrchestratorAgent SHALL stream progress updates as JSON_Line outputs
6. WHEN all agents complete, THE OrchestratorAgent SHALL emit a final JSON_Line with agent="orchestrator" and step="Complete"
7. THE final JSON_Line SHALL include done=true
8. THE final JSON_Line SHALL include Result_Payload with fields: proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
9. THE OrchestratorAgent SHALL NOT use markdown fencing in JSON responses

### Requirement 7: AWS AgentCore Integration

**User Story:** As a backend engineer, I want the Express backend to communicate with the agent service through AWS AgentCore, so that agent lifecycle and communication are properly managed.

#### Acceptance Criteria

1. THE Express_Backend SHALL connect to Agent_Service through AWS_AgentCore
2. THE AWS_AgentCore SHALL manage agent lifecycle
3. THE AWS_AgentCore SHALL handle communication between Express_Backend and Agent_Service
4. THE AWS_AgentCore SHALL run locally for development
5. THE Express_Backend SHALL NOT make direct HTTP calls to Agent_Service
6. THE Express_Backend SHALL use AWS_AgentCore client library for agent invocation

### Requirement 8: Express Backend SSE Proxy

**User Story:** As a frontend developer, I want the SSE endpoint to remain unchanged, so that the frontend requires zero modifications.

#### Acceptance Criteria

1. WHEN /api/forge/:grantId is requested, THE Forge_Endpoint SHALL fetch the full grant record from database by grantId
2. WHEN /api/forge/:grantId is requested, THE Forge_Endpoint SHALL fetch the full faculty list from database
3. THE Forge_Endpoint SHALL build POST /invoke payload with grantId, grantName, matchCriteria, eligibility, userProfile, facultyList
4. THE Forge_Endpoint SHALL send the payload through AWS_AgentCore to Agent_Service
5. THE Forge_Endpoint SHALL proxy-stream each JSON_Line from Agent_Service as SSE
6. WHEN receiving JSON_Line, THE Forge_Endpoint SHALL transform it to SSE format: data: { "step": "[AgentName]: [step description]", "done": false }
7. WHEN receiving final done=true JSON_Line, THE Forge_Endpoint SHALL forward Result_Payload as: data: { "step": "Complete", "done": true, "result": { ... } }
8. THE Forge_Endpoint SHALL preserve the existing SSE contract

### Requirement 9: Shared Schema Extension

**User Story:** As a TypeScript developer, I want type-safe schemas for the new result structure, so that the codebase maintains type safety.

#### Acceptance Criteria

1. THE /shared/routes.ts forge stream chunk schema SHALL include an optional result field
2. THE result field SHALL be a z.object with proposalDraft as z.string()
3. THE result field SHALL include collaborators as z.array of objects with name, department, expertise, relevanceScore
4. THE result field SHALL include matchScore as z.number()
5. THE result field SHALL include matchJustification as z.string()
6. THE result field SHALL include complianceChecklist as z.array of objects with task, category, and status
7. THE category enum SHALL include values: "RAMP", "COI", "IRB", "Policy"
8. THE status enum SHALL include values: "green", "yellow", "red"

### Requirement 10: Jupyter Notebook Testing Suite

**User Story:** As a data scientist, I want isolated notebooks for testing each agent, so that I can prototype and debug agents independently.

#### Acceptance Criteria

1. THE Agent_Service SHALL include 6 Jupyter notebooks in /notebooks/ directory
2. THE notebooks SHALL be named: 01_sourcing_agent.ipynb, 02_matchmaking_agent.ipynb, 03_collaborator_agent.ipynb, 04_drafting_agent.ipynb, 05_orchestrator_agent.ipynb, 06_full_pipeline.ipynb
3. WHEN executed, each notebook SHALL install dependencies: strands-agents, strands-agents-tools, boto3, fastapi, uvicorn
4. WHEN executed, each notebook SHALL configure BedrockModel with correct model_id
5. WHEN executed, each notebook SHALL define the agent's system prompt
6. WHEN executed, each notebook SHALL run a sample invocation using NSF GRFP and mock PhD student profile
7. WHEN executed, each notebook SHALL print streaming output step by step
8. WHEN executed, each notebook SHALL export final agent logic as importable Python function
9. THE 06_full_pipeline.ipynb notebook SHALL chain all agents and simulate complete forge pipeline

### Requirement 11: Environment Configuration

**User Story:** As a DevOps engineer, I want clear environment variable requirements, so that I can configure the system correctly.

#### Acceptance Criteria

1. THE system SHALL require AWS_REGION environment variable
2. THE system SHALL require AWS_ACCESS_KEY_ID environment variable
3. THE system SHALL require AWS_SECRET_ACCESS_KEY environment variable
4. THE system SHALL require AGENT_SERVICE_URL environment variable for Express backend
5. THE system SHALL support BEDROCK_MODEL_DRAFTING environment variable (default: anthropic.claude-sonnet-4-6)
6. THE system SHALL support BEDROCK_MODEL_FAST environment variable (default: anthropic.claude-haiku-4-5-20251001-v1:0)
7. WHERE environment is development, THE system SHALL load variables from .env file

### Requirement 12: Graceful Degradation

**User Story:** As a frontend developer, I want the system to never break during development, so that I can continue working even if the agent service is down.

#### Acceptance Criteria

1. IF AGENT_SERVICE_URL is unreachable, THEN THE Express_Backend SHALL fall back to mock steps
2. WHEN falling back to mock steps, THE Express_Backend SHALL log console.warn message
3. THE mock steps SHALL use the same SSE message format as real agent output
4. THE mock steps SHALL include realistic delays between steps
5. THE frontend SHALL never receive error responses due to agent service unavailability

### Requirement 13: Agent Service Containerization

**User Story:** As a DevOps engineer, I want the agent service to be containerized, so that deployment is consistent across environments.

#### Acceptance Criteria

1. THE Agent_Service SHALL include a Dockerfile
2. THE Dockerfile SHALL use Python 3.11 or later as base image
3. THE Dockerfile SHALL install all required dependencies from requirements.txt
4. THE Dockerfile SHALL expose port 8001
5. WHEN built, THE Docker image SHALL run uvicorn main:app --port 8001
6. THE Dockerfile SHALL include health check endpoint

### Requirement 14: Strands Agents Tool Usage

**User Story:** As a backend engineer, I want to use the Strands Agents tool correctly, so that all agents are properly configured and instantiated.

#### Acceptance Criteria

1. THE Agent_Service SHALL use Strands_Agents SDK for building all agents
2. THE Agent_Service SHALL import Agent from strands package
3. THE Agent_Service SHALL import BedrockModel from strands.models package
4. THE Agent_Service SHALL instantiate drafting_model with BedrockModel(model_id="anthropic.claude-sonnet-4-6")
5. THE Agent_Service SHALL instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
6. THE Agent_Service SHALL create sourcing_agent with Agent(model=fast_model, system_prompt="...")
7. THE Agent_Service SHALL create matchmaking_agent with Agent(model=fast_model, system_prompt="...")
8. THE Agent_Service SHALL create collaborator_agent with Agent(model=fast_model, system_prompt="...")
9. THE Agent_Service SHALL create drafting_agent with Agent(model=drafting_model, system_prompt="...")
10. THE Agent_Service SHALL create orchestrator_agent with Agent that coordinates all specialized agents

### Requirement 15: JSON Output Validation

**User Story:** As a frontend developer, I want all agent outputs to be valid JSON, so that parsing never fails.

#### Acceptance Criteria

1. THE Agent_Service SHALL NOT include markdown fencing in API responses
2. THE Agent_Service SHALL validate all JSON_Line outputs before streaming
3. IF an agent produces invalid JSON, THEN THE Agent_Service SHALL sanitize the output
4. THE Agent_Service SHALL ensure all string fields are properly escaped
5. THE Agent_Service SHALL ensure all numeric fields are valid numbers

### Requirement 16: Local Development Setup

**User Story:** As a developer, I want the full stack to run locally, so that I can develop and test the multi-agent integration without cloud dependencies.

#### Acceptance Criteria

1. THE system SHALL support running the full stack locally for development
2. THE Agent_Service SHALL run locally using uvicorn on port 8001
3. THE AWS_AgentCore SHALL run locally for development
4. THE Express_Backend SHALL connect to local AWS_AgentCore instance
5. THE system SHALL use local environment variables for AWS credentials
6. THE system SHALL provide clear documentation for local setup
7. WHERE environment is local development, THE system SHALL use localhost URLs for all service connections

### Requirement 17: Database Integration

**User Story:** As a backend engineer, I want the Express backend to fetch real data from the database, so that agents receive accurate grant and faculty information.

#### Acceptance Criteria

1. WHEN building /invoke payload, THE Express_Backend SHALL query grants table by grantId
2. WHEN building /invoke payload, THE Express_Backend SHALL query faculty table for all records
3. THE Express_Backend SHALL pass grant fields: name, targetAudience, eligibility, matchCriteria, internalDeadline
4. THE Express_Backend SHALL pass faculty fields: name, department, expertise, imageUrl, bio
5. THE Express_Backend SHALL pass facultyList as array in /invoke payload
6. IF grant is not found, THEN THE Express_Backend SHALL return error SSE message
7. THE Express_Backend SHALL use existing Drizzle ORM schema and queries
