# Implementation Plan: AWS Bedrock Backend Integration

## Overview

This implementation upgrades the FundingForge backend to integrate a real multi-agent AI pipeline powered by AWS Strands Agents SDK (Python). The system replaces hardcoded mock steps with a FastAPI microservice that orchestrates five specialized agents (SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent, OrchestratorAgent) using AWS Bedrock models. The Express backend connects to the agent service through AWS AgentCore and proxies streaming results via Server-Sent Events (SSE) while preserving all existing API contracts to ensure zero frontend changes. The full stack runs locally for development.

## Tasks

- [ ] 1. Set up Python agent service infrastructure
  - [ ] 1.1 Create agent-service directory structure
    - Create /agent-service/ directory at project root
    - Create /agent-service/agents/ subdirectory for agent implementations
    - Create /agent-service/notebooks/ subdirectory for Jupyter notebooks
    - Create requirements.txt with dependencies: fastapi, uvicorn, strands-agents, strands-agents-tools, boto3, pydantic, python-dotenv, tenacity
    - Create .env.example documenting AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BEDROCK_MODEL_DRAFTING, BEDROCK_MODEL_FAST
    - _Requirements: 1.1, 1.5, 11.1, 11.2, 11.3, 11.5, 11.6_
  
  - [ ] 1.2 Create Pydantic models in agent-service/models.py
    - Define UserProfile model with role, year, program fields
    - Define FacultyMember model with name, department, expertise, imageUrl, bio fields
    - Define InvokeRequest model with grantId, grantName, matchCriteria, eligibility, userProfile, facultyList fields
    - Define Collaborator model with name, department, expertise, relevanceScore fields
    - Define ComplianceItem model with task, category (RAMP|COI|IRB|Policy), status (green|yellow|red) fields
    - Define ResultPayload model with proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist fields
    - Define JSONLine model with agent, step, output, done fields
    - _Requirements: 1.3, 3.9, 6.8, 9.6, 9.7, 9.8_
  
  - [ ] 1.3 Create FastAPI app skeleton in agent-service/main.py
    - Import FastAPI and create app instance
    - Define POST /invoke endpoint that accepts InvokeRequest
    - Return StreamingResponse with media_type="application/x-ndjson"
    - Configure uvicorn to run on port 8001
    - Add environment variable validation at startup
    - _Requirements: 1.1, 1.2, 1.4, 11.7_
  
  - [ ]* 1.4 Write property test for endpoint existence
    - **Property 1: Agent service endpoint existence**
    - **Validates: Requirements 1.2**
  
  - [ ]* 1.5 Write property test for request payload validation
    - **Property 2: Request payload validation**
    - **Validates: Requirements 1.3**
  
  - [ ]* 1.6 Write unit tests for environment validation
    - Test missing AWS_REGION raises RuntimeError
    - Test missing AWS_ACCESS_KEY_ID raises RuntimeError
    - Test missing AWS_SECRET_ACCESS_KEY raises RuntimeError
    - _Requirements: 11.1, 11.2, 11.3_

- [ ] 2. Implement SourcingAgent
  - [ ] 2.1 Create agent-service/agents/sourcing.py
    - Import Agent and BedrockModel from strands packages
    - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    - Define system prompt for extracting user experience, publications, expertise, credentials
    - Create sourcing_agent with Agent(model=fast_model, system_prompt=...)
    - Implement run function that accepts userProfile and returns structured data
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 14.2, 14.3, 14.5, 14.6_
  
  - [ ] 2.2 Implement JSON_Line streaming for SourcingAgent
    - Yield JSON_Line with agent="sourcing", step="Extracting CV data...", output=None, done=False
    - Yield JSON_Line with agent="sourcing", step="Identified publications", output=None, done=False
    - Yield final JSON_Line with agent="sourcing", step="Complete", output={structured data}, done=True
    - _Requirements: 2.6, 2.7_
  
  - [ ]* 2.3 Write property test for SourcingAgent model configuration
    - **Property 5: SourcingAgent model configuration**
    - **Validates: Requirements 2.1**
  
  - [ ]* 2.4 Write property test for SourcingAgent data extraction
    - **Property 6: SourcingAgent data extraction**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**
  
  - [ ]* 2.5 Write unit tests for SourcingAgent
    - Test uses correct Haiku model ID
    - Test extracts experience from sample profile
    - Test returns structured data with required fields
    - Test emits done=true on completion
    - _Requirements: 2.1, 2.5, 2.7_

- [ ] 3. Implement MatchmakingAgent
  - [ ] 3.1 Create agent-service/agents/matchmaking.py
    - Import Agent and BedrockModel from strands packages
    - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    - Define system prompt for dual responsibility: match analysis AND compliance checking (FSU policies, RAMP, COI, IRB)
    - Create matchmaking_agent with Agent(model=fast_model, system_prompt=...)
    - Implement run function that accepts userProfile, sourcedData, matchCriteria, eligibility
    - Return matchScore (0-100), matchJustification, complianceChecklist
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 14.7_
  
  - [ ] 3.2 Implement JSON_Line streaming for MatchmakingAgent
    - Yield JSON_Line with agent="matchmaking", step="Analyzing match criteria...", output=None, done=False
    - Yield JSON_Line with agent="matchmaking", step="Checking FSU policies...", output=None, done=False
    - Yield JSON_Line with agent="matchmaking", step="Checking RAMP requirements...", output=None, done=False
    - Yield JSON_Line with agent="matchmaking", step="Identifying COI triggers...", output=None, done=False
    - Yield JSON_Line with agent="matchmaking", step="Checking IRB requirements...", output=None, done=False
    - Yield JSON_Line with agent="matchmaking", step="Match score: X%", output=None, done=False
    - Yield final JSON_Line with agent="matchmaking", step="Complete", output={matchScore, matchJustification, complianceChecklist}, done=True
    - _Requirements: 3.10, 3.11_
  
  - [ ]* 3.3 Write property test for MatchmakingAgent model configuration
    - **Property 9: MatchmakingAgent model configuration**
    - **Validates: Requirements 3.1**
  
  - [ ]* 3.4 Write property test for match score range validation
    - **Property 11: Match score range validation**
    - **Validates: Requirements 3.7**
  
  - [ ]* 3.5 Write property test for compliance checklist structure
    - **Property 13: Compliance checklist structure**
    - **Validates: Requirements 3.9**
  
  - [ ]* 3.6 Write unit tests for MatchmakingAgent
    - Test uses correct Haiku model ID
    - Test returns match score in range [0, 100]
    - Test includes compliance checklist with RAMP item
    - Test includes compliance checklist with COI item
    - Test includes compliance checklist with IRB item
    - Test includes compliance checklist with Policy item
    - Test includes non-empty match justification
    - _Requirements: 3.1, 3.7, 3.8, 3.9_

- [ ] 4. Implement CollaboratorAgent
  - [ ] 4.1 Create agent-service/agents/collaborator.py
    - Import Agent and BedrockModel from strands packages
    - Instantiate fast_model with BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    - Define system prompt for matching faculty based on program and expertise keywords
    - Create collaborator_agent with Agent(model=fast_model, system_prompt=...)
    - Implement run function that accepts facultyList, matchCriteria, userProfile
    - Return top 3 faculty members with name, department, expertise, relevanceScore
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 14.8_
  
  - [ ] 4.2 Implement JSON_Line streaming for CollaboratorAgent
    - Yield JSON_Line with agent="collaborator", step="Analyzing faculty expertise...", output=None, done=False
    - Yield JSON_Line with agent="collaborator", step="Matching against grant criteria...", output=None, done=False
    - Yield JSON_Line with agent="collaborator", step="Found X relevant collaborators", output=None, done=False
    - Yield final JSON_Line with agent="collaborator", step="Complete", output={collaborators}, done=True
    - _Requirements: 5.6, 5.7_
  
  - [ ]* 4.3 Write property test for CollaboratorAgent model configuration
    - **Property 18: CollaboratorAgent model configuration**
    - **Validates: Requirements 5.1**
  
  - [ ]* 4.4 Write property test for top collaborators limit
    - **Property 21: Top collaborators limit**
    - **Validates: Requirements 5.4**
  
  - [ ]* 4.5 Write unit tests for CollaboratorAgent
    - Test uses correct Haiku model ID
    - Test returns at most 3 collaborators
    - Test each collaborator has relevance score
    - _Requirements: 5.1, 5.4, 5.5_

- [ ] 5. Implement DraftingAgent
  - [ ] 5.1 Create agent-service/agents/drafting.py
    - Import Agent and BedrockModel from strands packages
    - Instantiate drafting_model with BedrockModel(model_id="anthropic.claude-sonnet-4-6")
    - Define system prompt for generating high-quality proposal narrative with section headers
    - Create drafting_agent with Agent(model=drafting_model, system_prompt=...)
    - Implement run function that accepts grantName, matchCriteria, eligibility, matchJustification, sourcedData, collaborators
    - Return proposalDraft (300-500 words with section headers)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7, 14.4, 14.9_
  
  - [ ] 5.2 Implement JSON_Line streaming for DraftingAgent
    - Yield JSON_Line with agent="drafting", step="Generating proposal structure...", output=None, done=False
    - Yield JSON_Line with agent="drafting", step="Writing introduction...", output=None, done=False
    - Yield JSON_Line with agent="drafting", step="Drafting methodology section...", output=None, done=False
    - Yield JSON_Line with agent="drafting", step="Generated X-word draft", output=None, done=False
    - Yield final JSON_Line with agent="drafting", step="Complete", output={proposalDraft}, done=True
    - _Requirements: 4.5, 4.6_
  
  - [ ]* 5.3 Write property test for DraftingAgent model configuration
    - **Property 14: DraftingAgent model configuration**
    - **Validates: Requirements 4.1**
  
  - [ ]* 5.4 Write property test for proposal word count constraint
    - **Property 16: Proposal word count constraint**
    - **Validates: Requirements 4.3**
  
  - [ ]* 5.5 Write unit tests for DraftingAgent
    - Test uses correct Sonnet model ID
    - Test generates proposal with section headers
    - Test proposal is between 300-500 words
    - _Requirements: 4.1, 4.3, 4.4_

- [ ] 6. Checkpoint - Ensure all agent implementations pass tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement OrchestratorAgent
  - [ ] 7.1 Create agent-service/agents/orchestrator.py
    - Import all specialized agents (sourcing, matchmaking, collaborator, drafting)
    - Define orchestrate_pipeline async function that accepts InvokeRequest
    - Implement sequential execution: SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
    - Pass outputs from each agent to subsequent agents as needed
    - Yield progress JSON_Line messages after each agent completes
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 14.10_
  
  - [ ] 7.2 Implement final result aggregation
    - After all agents complete, construct Result_Payload with proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
    - Yield final JSON_Line with agent="orchestrator", step="Complete", output=Result_Payload, done=True
    - Ensure no markdown fencing in JSON responses
    - _Requirements: 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 7.3 Write property test for agent execution order
    - **Property 24: Agent execution order**
    - **Validates: Requirements 6.2**
  
  - [ ]* 7.4 Write property test for complete result payload
    - **Property 28: Complete result payload**
    - **Validates: Requirements 6.8**
  
  - [ ]* 7.5 Write property test for no markdown fencing
    - **Property 29: No markdown fencing in JSON**
    - **Validates: Requirements 6.9, 15.1**
  
  - [ ]* 7.6 Write unit tests for OrchestratorAgent
    - Test executes all 4 agents in correct order
    - Test final message has agent="orchestrator"
    - Test final message includes complete Result_Payload
    - Test passes sourced data to MatchmakingAgent
    - Test passes collaborators to DraftingAgent
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 6.8_

- [ ] 8. Wire OrchestratorAgent to FastAPI endpoint
  - [ ] 8.1 Update agent-service/main.py to use OrchestratorAgent
    - Import orchestrate_pipeline from agents/orchestrator.py
    - In POST /invoke endpoint, call orchestrate_pipeline with request payload
    - Stream JSON_Line outputs as newline-delimited JSON
    - Add error handling for agent execution failures
    - Sanitize all JSON_Line outputs before streaming
    - _Requirements: 1.2, 15.2, 15.3, 15.4, 15.5_
  
  - [ ]* 8.2 Write property test for JSON_Line streaming format
    - **Property 7: JSON_Line streaming format**
    - **Validates: Requirements 2.6, 3.10, 4.5, 5.6**
  
  - [ ]* 8.3 Write property test for agent completion signaling
    - **Property 8: Agent completion signaling**
    - **Validates: Requirements 2.7, 3.11, 4.6, 5.7**
  
  - [ ]* 8.4 Write property test for JSON output validity
    - **Property 39: JSON output validity**
    - **Validates: Requirements 15.2, 15.3, 15.4, 15.5**

- [ ] 9. Create Jupyter notebooks for agent testing
  - [ ] 9.1 Create 01_sourcing_agent.ipynb
    - Install dependencies: strands-agents, strands-agents-tools, boto3
    - Configure BedrockModel with Haiku model ID
    - Define SourcingAgent system prompt
    - Run sample invocation using mock PhD student profile
    - Print streaming output step by step
    - Export agent logic as importable Python function
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [ ] 9.2 Create 02_matchmaking_agent.ipynb
    - Install dependencies and configure BedrockModel with Haiku model ID
    - Define MatchmakingAgent system prompt for match analysis and compliance checking
    - Run sample invocation using NSF GRFP grant and mock profile
    - Print streaming output including match score and compliance checklist
    - Export agent logic as importable Python function
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [ ] 9.3 Create 03_collaborator_agent.ipynb
    - Install dependencies and configure BedrockModel with Haiku model ID
    - Define CollaboratorAgent system prompt
    - Run sample invocation with mock faculty list
    - Print streaming output showing top 3 collaborators with relevance scores
    - Export agent logic as importable Python function
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [ ] 9.4 Create 04_drafting_agent.ipynb
    - Install dependencies and configure BedrockModel with Sonnet model ID
    - Define DraftingAgent system prompt
    - Run sample invocation with grant context and match justification
    - Print streaming output showing proposal draft with section headers
    - Verify word count is between 300-500 words
    - Export agent logic as importable Python function
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [ ] 9.5 Create 05_orchestrator_agent.ipynb
    - Install dependencies including fastapi and uvicorn
    - Import all specialized agents
    - Define orchestration logic that chains all agents
    - Run sample invocation showing complete pipeline execution
    - Print streaming output from all agents in sequence
    - Export orchestrator logic as importable Python function
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_
  
  - [ ] 9.6 Create 06_full_pipeline.ipynb
    - Import all agents and orchestrator
    - Simulate complete forge pipeline from request to result
    - Use NSF GRFP grant and mock PhD student profile
    - Print all JSON_Line outputs in sequence
    - Verify final Result_Payload contains all required fields
    - Document expected output format and timing
    - _Requirements: 10.1, 10.2, 10.9_

- [ ] 10. Checkpoint - Verify agent service runs locally
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement AWS AgentCore integration in Express backend
  - [ ] 11.1 Install AgentCore client library
    - Add @aws-sdk/client-agentcore to package.json dependencies
    - Add fast-check to devDependencies for property-based testing
    - Update .env.example with AGENT_SERVICE_URL and AGENTCORE_ENDPOINT variables
    - _Requirements: 7.6, 11.4_
  
  - [ ] 11.2 Create server/agentcore-client.ts
    - Import AgentCoreClient from @aws-sdk/client-agentcore
    - Configure client with AWS_REGION and AGENTCORE_ENDPOINT from environment
    - Implement invokeAgentPipeline async generator function
    - Accept InvokePayload and stream JSON_Line responses
    - Use AgentCore client (NOT direct HTTP calls)
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_
  
  - [ ]* 11.3 Write property test for AgentCore URL configuration
    - **Property 3: AgentCore URL configuration**
    - **Validates: Requirements 1.7**
  
  - [ ]* 11.4 Write property test for AgentCore integration
    - **Property 30: AgentCore integration**
    - **Validates: Requirements 7.1, 7.5**
  
  - [ ]* 11.5 Write unit tests for AgentCore client
    - Test uses AgentCore client for invocation
    - Test does not make direct HTTP calls
    - Test uses AGENT_SERVICE_URL from environment
    - Test uses AGENTCORE_ENDPOINT from environment (default: http://localhost:8000)
    - _Requirements: 7.1, 7.5, 7.6, 11.4_

- [ ] 12. Update Express backend forge endpoint
  - [ ] 12.1 Update server/routes.ts /api/forge/:grantId endpoint
    - Import invokeAgentPipeline from server/agentcore-client.ts
    - Extract grantId from URL path parameters
    - Extract role, year, program from query parameters
    - Fetch grant record from storage by grantId
    - Fetch full faculty list from storage
    - Handle grant not found with error SSE message
    - _Requirements: 8.1, 8.2, 17.1, 17.2, 17.6, 17.7_
  
  - [ ] 12.2 Build complete InvokePayload
    - Construct payload with grantId, grantName, matchCriteria, eligibility from grant record
    - Add userProfile with role, year, program from query parameters
    - Add facultyList with name, department, expertise, imageUrl, bio fields
    - Ensure all required fields are included
    - _Requirements: 8.3, 17.3, 17.4, 17.5_
  
  - [ ] 12.3 Implement SSE proxy streaming
    - Invoke agent pipeline through AgentCore with payload
    - For each JSON_Line received, transform to SSE format
    - For non-final JSON_Line: { step: "[AgentName]: [step]", done: false }
    - For final JSON_Line: { step: "Complete", done: true, result: {...} }
    - Stream each SSE message to client
    - _Requirements: 8.4, 8.5, 8.6, 8.7, 8.8_
  
  - [ ] 12.4 Implement graceful degradation with mock fallback
    - Wrap agent invocation in try-catch block
    - If agent service unreachable, log console.warn message
    - Fall back to mock steps with same SSE format
    - Send mock progress messages with realistic delays
    - Send mock result with sample proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
    - Ensure frontend never receives error responses due to service unavailability
    - _Requirements: 1.8, 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ]* 12.5 Write property test for graceful degradation
    - **Property 4: Graceful degradation on service failure**
    - **Validates: Requirements 1.8, 12.1, 12.2**
  
  - [ ]* 12.6 Write property test for forge endpoint database queries
    - **Property 31: Forge endpoint database queries**
    - **Validates: Requirements 8.1, 8.2, 17.1, 17.2**
  
  - [ ]* 12.7 Write property test for complete payload construction
    - **Property 32: Complete payload construction**
    - **Validates: Requirements 8.3, 17.3, 17.4, 17.5**
  
  - [ ]* 12.8 Write property test for SSE format transformation
    - **Property 34: SSE format transformation**
    - **Validates: Requirements 8.6, 8.7**
  
  - [ ]* 12.9 Write property test for mock fallback SSE compatibility
    - **Property 35: Mock fallback SSE compatibility**
    - **Validates: Requirements 12.3**
  
  - [ ]* 12.10 Write unit tests for forge endpoint
    - Test fetches grant by grantId
    - Test fetches faculty list
    - Test returns error SSE for invalid grantId
    - Test falls back to mock steps when agent service unreachable
    - Test logs console.warn on fallback
    - Test transforms JSON_Line to SSE format
    - _Requirements: 8.1, 8.2, 8.6, 12.1, 12.2, 17.1, 17.2_

- [ ] 13. Update shared schema with new result fields
  - [ ] 13.1 Update shared/routes.ts forgeStreamChunkSchema
    - Add optional result field as z.object()
    - Add result.proposalDraft as z.string()
    - Add result.collaborators as z.array() with name, department, expertise, relevanceScore fields
    - Add result.matchScore as z.number().min(0).max(100)
    - Add result.matchJustification as z.string()
    - Add result.complianceChecklist as z.array() with task, category, status fields
    - Define category enum: "RAMP", "COI", "IRB", "Policy"
    - Define status enum: "green", "yellow", "red"
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_
  
  - [ ]* 13.2 Write unit tests for schema validation
    - Test forgeStreamChunkSchema includes result field
    - Test result.proposalDraft is z.string()
    - Test result.collaborators is array with correct structure
    - Test result.matchScore is z.number()
    - Test result.complianceChecklist has correct enum values
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [ ] 14. Checkpoint - Ensure Express backend integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Add environment validation to Express backend
  - [ ] 15.1 Update server/index.ts with environment validation
    - Check for required variables: DATABASE_URL, AGENT_SERVICE_URL, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - Log clear error messages identifying missing variables
    - Exit process with non-zero code if validation fails
    - Load dotenv in development mode before validation
    - Support optional BEDROCK_MODEL_DRAFTING and BEDROCK_MODEL_FAST variables with defaults
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_
  
  - [ ]* 15.2 Write property test for model configuration with environment variables
    - **Property 38: Model configuration with environment variables**
    - **Validates: Requirements 11.5, 11.6**
  
  - [ ]* 15.3 Write unit tests for environment validation
    - Test exits on missing DATABASE_URL
    - Test exits on missing AGENT_SERVICE_URL
    - Test exits on missing AWS_REGION
    - Test uses default model IDs when env vars not set
    - Test uses custom model IDs when env vars set
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 16. Create Docker containerization for agent service
  - [ ] 16.1 Create agent-service/Dockerfile
    - Use Python 3.11 or later as base image
    - Copy requirements.txt and install dependencies
    - Copy all agent service code
    - Expose port 8001
    - Set CMD to run uvicorn main:app --host 0.0.0.0 --port 8001
    - Add health check endpoint
    - _Requirements: 1.6, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 16.2 Test Docker build and run
    - Build Docker image
    - Run container with environment variables
    - Verify /invoke endpoint is accessible
    - Verify health check endpoint responds
    - _Requirements: 13.5, 13.6_

- [ ] 17. Create documentation and local development setup guide
  - [ ] 17.1 Create agent-service/README.md
    - Document required environment variables
    - Provide example .env configuration
    - Document required IAM permissions for Bedrock access
    - Include local development setup instructions
    - Document how to run Jupyter notebooks
    - Include cost considerations and monitoring recommendations
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6, 16.6_
  
  - [ ] 17.2 Update project root README.md
    - Document full stack local development setup
    - Provide instructions for starting PostgreSQL, agent service, AgentCore, Express backend
    - Document localhost URLs for all services
    - Include troubleshooting section for common issues
    - Document graceful degradation behavior
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_
  
  - [ ] 17.3 Add inline code documentation
    - Add JSDoc comments to invokeAgentPipeline function
    - Add JSDoc comments to InvokePayload interface
    - Add docstrings to all Python agent classes
    - Add docstrings to orchestrate_pipeline function
    - Document error handling strategy in comments
    - _Requirements: 1.3, 6.8_

- [ ] 18. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests use fast-check (TypeScript) and hypothesis (Python) with minimum 100 iterations
- The implementation uses Strands Agents SDK for all agent construction
- All agents stream progress as JSON_Line format
- Express backend connects through AWS AgentCore (not direct HTTP)
- Full stack runs locally for development
- Graceful degradation ensures zero downtime if agent service is unavailable
- 6 Jupyter notebooks provide isolated testing for each agent plus full pipeline
- Result schema includes matchScore, matchJustification, and complianceChecklist with categories
