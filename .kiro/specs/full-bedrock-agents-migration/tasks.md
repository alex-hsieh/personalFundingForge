# Implementation Plan: Full Bedrock Agents Migration

## Overview

This implementation plan migrates FundingForge from Strands Agents + FastAPI to AWS Bedrock Agents with Knowledge Base integration. The work is structured for 2 developers working in parallel to complete the migration in 2-3 weeks.

**Timeline:** 2-3 weeks with 2 developers  
**Developer A:** AWS Infrastructure (Bedrock Agents, Knowledge Base, Lambda Action Groups)  
**Developer B:** Express Backend (AWS SDK integration, testing, cleanup)

## Parallel Development Tracks

### Track A: AWS Infrastructure (Developer A)
Focus: Bedrock Agents, Knowledge Base, Lambda Action Groups, IAM roles

### Track B: Express Backend (Developer B)
Focus: Express backend refactoring, AWS SDK integration, testing

### Integration Point: End of Week 2
Both developers integrate their work and test the complete pipeline together.

## Tasks

- [x] 1. Track A - Week 1: AWS Infrastructure Foundation (Developer A)
  - Set up Bedrock Agents, Knowledge Base, and IAM roles
  - _Estimated time: 1 day_
  - _Requirements: 1.1, 1.2, 1.3, 2.1-2.8, 3.1-3.9, 12.1-12.9_


  - [ ] 1.1 Create Bedrock Supervisor Agent
    - Create agent in AWS Bedrock console with name "FundingForge-Supervisor"
    - Configure with Claude 3.5 Sonnet foundation model (anthropic.claude-3-5-sonnet-20241022-v2:0)
    - Add orchestration instructions from design document
    - Create DRAFT alias for development
    - Document agent ID and ARN
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 1.2 Create Bedrock Sub-Agents
    - Create Sourcing Agent with user profile extraction instructions
    - Create Matchmaking Agent with grant analysis instructions
    - Create Collaborator Agent with faculty ranking instructions
    - Create Drafting Agent with proposal generation instructions
    - Configure all with Claude 3.5 Sonnet
    - Create DRAFT aliases for all agents
    - Document all agent IDs and ARNs
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.8_

  - [ ] 1.3 Set up Knowledge Base infrastructure
    - Create S3 bucket "fundingforge-knowledge-base" with versioning enabled
    - Create directory structure: policies/, templates/, compliance/
    - Enable S3 encryption at rest using AWS KMS
    - Create OpenSearch Serverless collection "fundingforge-vectors"
    - Configure vector store with 1024 dimensions for Titan Embed Text v2
    - _Requirements: 3.1, 3.4, 3.5, 12.7_

  - [ ] 1.4 Create and configure Knowledge Base
    - Create Knowledge Base "FundingForgeKnowledgeBase" in Bedrock
    - Configure with Amazon Titan Embed Text v2 embedding model
    - Link to OpenSearch Serverless collection
    - Configure S3 data source with chunking strategy (300 tokens, 20% overlap)
    - Set up IAM role for Knowledge Base with S3 read and OpenSearch write permissions
    - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.9, 12.4_

  - [ ] 1.5 Upload initial grant documents and start ingestion
    - Upload sample documents to S3 (policies, templates, compliance docs)
    - Start ingestion job via AWS CLI or Python script
    - Monitor ingestion job status until complete
    - Test retrieval queries to verify documents are searchable
    - _Requirements: 3.5, 3.7_

  - [ ] 1.6 Configure IAM roles for all agents
    - Create IAM role for Supervisor Agent with permissions to invoke Sub-Agents
    - Create IAM roles for Sub-Agents with permissions to invoke foundation models
    - Add Knowledge Base retrieval permission to Matchmaking Agent role
    - Configure trust relationships for all roles
    - Test permissions with sample agent invocations
    - _Requirements: 1.8, 12.1, 12.2, 12.3_

- [ ] 2. Track A - Week 2: Lambda Action Groups (Developer A)
  - Implement custom business logic as Lambda functions
  - _Estimated time: 4 days_
  - _Requirements: 4.1-4.10, 12.5_

  - [ ] 2.1 Implement Faculty Ranking Lambda
    - Create Python Lambda function with ranking algorithm
    - Implement calculate_match_score function using keyword matching
    - Write OpenAPI 3.0 schema for /rankFaculty endpoint
    - Deploy to AWS Lambda with 512MB memory, 30s timeout
    - Create IAM role with CloudWatch Logs permissions
    - Unit test with sample faculty lists
    - _Requirements: 4.1, 4.7, 4.10_

  - [ ]* 2.2 Write unit tests for Faculty Ranking Lambda
    - Test ranking algorithm with various faculty expertise combinations
    - Test edge cases: empty faculty list, no matching expertise
    - Test score calculation accuracy
    - Verify OpenAPI schema compliance
    - _Requirements: 10.1_

  - [ ] 2.3 Implement Compliance Checker Lambda
    - Create Python Lambda function with compliance validation logic
    - Implement validate_task and check_missing_critical_tasks functions
    - Write OpenAPI 3.0 schema for /checkCompliance endpoint
    - Deploy to AWS Lambda with 256MB memory, 15s timeout
    - Create IAM role with CloudWatch Logs permissions
    - Unit test with sample compliance checklists
    - _Requirements: 4.2, 4.8, 4.10_

  - [ ]* 2.4 Write unit tests for Compliance Checker Lambda
    - Test validation logic for each compliance category (RAMP, COI, IRB, Policy)
    - Test missing critical task detection
    - Test status assignment (green, yellow, red)
    - Verify OpenAPI schema compliance
    - _Requirements: 10.1_

  - [ ] 2.5 Implement Proposal Formatter Lambda
    - Create Python Lambda function with formatting logic
    - Implement format_proposal and clean_paragraph functions
    - Write OpenAPI 3.0 schema for /formatProposal endpoint
    - Deploy to AWS Lambda with 256MB memory, 15s timeout
    - Create IAM role with CloudWatch Logs permissions
    - Unit test with sample proposal drafts
    - _Requirements: 4.3, 4.9, 4.10_

  - [ ]* 2.6 Write unit tests for Proposal Formatter Lambda
    - Test formatting with various proposal structures
    - Test section organization and header insertion
    - Test paragraph cleaning and whitespace normalization
    - Verify OpenAPI schema compliance
    - _Requirements: 10.1_

  - [ ] 2.7 Link Action Groups to Bedrock Agents
    - Link Faculty Ranking Lambda to Collaborator Agent
    - Link Compliance Checker Lambda to Matchmaking Agent
    - Link Proposal Formatter Lambda to Drafting Agent
    - Configure OpenAPI schemas in agent action group settings
    - Test action group invocations from agents
    - _Requirements: 4.7, 4.8, 4.9_

- [ ] 3. Track A - Week 2: Agent Integration Testing (Developer A)
  - Test complete agent pipeline via AWS Console
  - _Estimated time: 1 day_
  - _Requirements: 1.4, 1.5, 1.6, 1.7, 2.5, 2.6_

  - [ ] 3.1 Test Supervisor Agent orchestration
    - Invoke Supervisor Agent via AWS Console with test payload
    - Verify all 4 Sub-Agents are invoked in sequence
    - Verify session state is preserved across sub-agent invocations
    - Verify progress updates are emitted after each sub-agent
    - Verify final output contains all required fields
    - _Requirements: 1.4, 1.5, 1.6, 1.7_

  - [ ] 3.2 Test Knowledge Base retrieval in Matchmaking Agent
    - Invoke Matchmaking Agent with grant criteria
    - Verify Knowledge Base retrieval returns relevant documents (up to 10)
    - Verify hybrid search combines semantic and keyword matching
    - Test with various query types
    - _Requirements: 3.8_

  - [ ] 3.3 Test Action Group invocations
    - Verify Collaborator Agent successfully invokes Faculty Ranking Lambda
    - Verify Matchmaking Agent successfully invokes Compliance Checker Lambda
    - Verify Drafting Agent successfully invokes Proposal Formatter Lambda
    - Verify structured JSON responses are returned
    - _Requirements: 4.4, 4.5_

  - [ ] 3.4 Document AWS infrastructure configuration
    - Create configuration document with all agent IDs and ARNs
    - Document Lambda function ARNs
    - Document Knowledge Base ID and data source ID
    - Create environment variable template for Developer B
    - Write setup instructions and troubleshooting guide
    - _Requirements: 14.1, 14.2, 14.3_

- [ ] 4. Track B - Week 1: Express Backend Setup (Developer B)
  - Install dependencies and configure AWS credentials
  - _Estimated time: 2 days_
  - _Requirements: 5.1, 5.10, 7.1, 7.2, 7.3_

  - [ ] 4.1 Install AWS SDK and configure dependencies
    - Install @aws-sdk/client-bedrock-agent-runtime package
    - Update package.json with AWS SDK dependency
    - Run npm install to update package-lock.json
    - Verify installation with import test
    - _Requirements: 5.1_

  - [ ] 4.2 Configure AWS credentials for local development
    - Set up AWS credentials via environment variables or AWS CLI profile
    - Create .env file with AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - Update .env.example with AWS configuration template
    - Test BedrockAgentRuntimeClient initialization
    - Document credential setup in README
    - _Requirements: 5.10, 7.1, 7.2, 7.6_

  - [ ] 4.3 Add environment variables for Bedrock configuration
    - Add BEDROCK_SUPERVISOR_AGENT_ID to .env
    - Add BEDROCK_AGENT_ALIAS_ID to .env (default: TSTALIASID)
    - Add USE_BEDROCK_AGENTS feature flag (default: false)
    - Add COMPARE_IMPLEMENTATIONS flag for validation (default: false)
    - Update .env.example with all new variables
    - _Requirements: 7.3, 7.7_

- [ ] 5. Track B - Week 1-2: Refactor agent-client.ts (Developer B)
  - Replace HTTP calls with AWS SDK InvokeAgent API
  - _Estimated time: 3 days_
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 15.1-15.10_

  - [ ] 5.1 Initialize BedrockAgentRuntimeClient
    - Import BedrockAgentRuntimeClient and InvokeAgentCommand from AWS SDK
    - Initialize client with region from environment variable
    - Configure automatic credential loading (env vars, IAM role, AWS CLI profile)
    - Add health check function to verify agent availability
    - _Requirements: 5.1, 5.10_

  - [ ] 5.2 Refactor invokeAgentPipeline to use InvokeAgent API
    - Replace HTTP fetch with InvokeAgentCommand
    - Generate unique session ID for each invocation
    - Pass all payload fields as session attributes (grantId, grantName, matchCriteria, eligibility, userProfile, facultyList)
    - Set enableTrace: true for observability
    - Maintain AsyncGenerator<JSONLine> return type for frontend compatibility
    - _Requirements: 5.2, 5.3, 5.4, 5.7, 5.9, 15.1, 15.2_

  - [ ] 5.3 Implement streaming response parsing
    - Parse Bedrock Agent completion stream events
    - Handle chunk events (agent output)
    - Handle trace events (for observability logging)
    - Handle returnControl events (agent requesting action)
    - Buffer incomplete JSON lines and parse when complete
    - _Requirements: 5.5, 5.6_

  - [ ] 5.4 Convert Bedrock events to JSONLine format
    - Convert each Bedrock event to JSONLine with agent, step, output, done fields
    - Detect current agent from parsed data
    - Emit progress updates as JSONLine events
    - Emit final aggregated result with done: true
    - Maintain SSE event structure for frontend compatibility
    - _Requirements: 5.6, 15.2, 15.3, 15.4_

  - [ ] 5.5 Implement error handling
    - Handle network errors with retry logic
    - Handle timeout errors (30 second timeout)
    - Handle invalid response format errors
    - Handle AWS credential errors with helpful messages
    - Emit errors as JSONLine events with error field
    - Return appropriate HTTP status codes (400, 401, 403, 500, 503, 504)
    - _Requirements: 5.8, 15.5_

  - [ ] 5.6 Add trace logging for observability
    - Log session ID, input parameters, and timestamp on invocation
    - Log token usage from trace events
    - Log agent transitions and progress updates
    - Log errors with full context
    - Log completion with execution duration
    - _Requirements: 5.7, 11.1, 11.3, 11.4, 11.5, 11.9_

- [ ] 6. Track B - Week 2: Testing (Developer B)
  - Write comprehensive unit tests for Express backend
  - _Estimated time: 2 days_
  - _Requirements: 10.1, 10.2, 10.9_

  - [ ] 6.1 Write unit tests for agent-client.ts
    - Test invokeAgentPipeline with mocked Bedrock responses
    - Test session attribute passing
    - Test streaming response parsing
    - Test JSONLine conversion
    - Test error handling scenarios
    - Achieve > 80% code coverage
    - _Requirements: 10.1_

  - [ ]* 6.2 Write unit tests for stream parsing
    - Test parsing of chunk events
    - Test parsing of trace events
    - Test buffering of incomplete JSON lines
    - Test handling of malformed events
    - _Requirements: 10.1_

  - [ ]* 6.3 Write unit tests for error handling
    - Test network error handling and retry logic
    - Test timeout error handling
    - Test credential error handling
    - Test invalid response format handling
    - Verify appropriate error messages and status codes
    - _Requirements: 10.1, 10.9_

- [ ] 7. Track B - Week 2: Cleanup and Documentation (Developer B)
  - Remove FastAPI dependencies and update documentation
  - _Estimated time: 1 day_
  - _Requirements: 6.1-6.10, 14.1-14.10_

  - [ ] 7.1 Remove FastAPI service references
    - Remove AGENT_SERVICE_URL from .env and .env.example
    - Remove HTTP fetch calls to port 8001
    - Remove any FastAPI-specific error handling
    - _Requirements: 6.8, 6.9_

  - [ ] 7.2 Update documentation
    - Update README with AWS Bedrock setup instructions
    - Update ARCHITECTURE.md with new Bedrock Agents architecture
    - Document environment variable configuration
    - Add troubleshooting guide for common AWS issues
    - _Requirements: 14.1, 14.2, 14.6, 14.9_

  - [ ] 7.3 Prepare for integration with Developer A
    - Review configuration document from Developer A
    - Prepare test payloads for integration testing
    - Document any blocking issues or questions
    - _Requirements: 8.4_

- [ ] 8. Checkpoint - Week 2 End: Integration Handoff
  - Both developers sync and prepare for integration testing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 9. Integration Phase - Week 3: End-to-End Testing (Both Developers)
  - Integrate AWS infrastructure with Express backend
  - _Estimated time: 5 days_
  - _Requirements: 8.4, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [ ] 9.1 Configure Express backend with production agent IDs
    - Update .env with agent IDs from Developer A's configuration document
    - Update BEDROCK_SUPERVISOR_AGENT_ID
    - Update BEDROCK_AGENT_ALIAS_ID
    - Update KNOWLEDGE_BASE_ID
    - Verify all environment variables are set correctly
    - _Requirements: 8.4_

  - [ ] 9.2 Test end-to-end pipeline
    - Start Express backend with USE_BEDROCK_AGENTS=true
    - Invoke /api/invoke endpoint with test payload
    - Verify SSE stream delivers events in correct order
    - Verify final event contains all required fields
    - Verify frontend receives and displays results correctly
    - _Requirements: 10.3, 15.6, 15.7, 15.8_

  - [ ]* 9.3 Write integration tests for full pipeline
    - Test complete proposal generation flow
    - Verify all 4 sub-agents are invoked
    - Verify final output structure matches schema
    - Test with various grant types and user profiles
    - Measure end-to-end latency (target: < 30 seconds)
    - _Requirements: 10.2, 10.6, 10.7, 10.8_

  - [ ] 9.4 Debug integration issues
    - Review CloudWatch logs for agent errors
    - Check IAM permissions if invocation fails
    - Verify session state is passed correctly
    - Test Knowledge Base retrieval
    - Test Action Group invocations
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 10. Integration Phase - Week 3: Property-Based Testing (Both Developers)
  - Implement and run property tests for correctness properties
  - _Estimated time: 2 days_
  - _Requirements: 10.1, 10.2_

  - [ ]* 10.1 Write property test for final output completeness
    - **Property 2: Final Output Contains All Required Fields**
    - **Validates: Requirements 1.5**
    - Use fast-check to generate random valid payloads
    - Verify final output always contains proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
    - Run 100 iterations
    - _Requirements: 10.2_

  - [ ]* 10.2 Write property test for JSONLine format consistency
    - **Property 15: Bedrock to JSONLine Conversion**
    - **Validates: Requirements 5.6**
    - Verify all events have agent, step, output, done fields
    - Verify field types are correct
    - Run 100 iterations
    - _Requirements: 10.2_

  - [ ]* 10.3 Write property test for session attributes
    - **Property 13: Session Attributes Passed Completely**
    - **Validates: Requirements 5.4**
    - Mock Bedrock client to capture InvokeAgentCommand
    - Verify all payload fields are passed as session attributes
    - Verify JSON stringification for userProfile and facultyList
    - Run 100 iterations
    - _Requirements: 10.2_

  - [ ]* 10.4 Write property test for sub-agent invocation
    - **Property 1: Supervisor Agent Invokes All Sub-Agents**
    - **Validates: Requirements 1.4**
    - Verify all 4 sub-agents are invoked in sequence
    - Use CloudWatch logs or trace events to verify
    - Run 100 iterations
    - _Requirements: 10.2, 10.6_

  - [ ]* 10.5 Write property test for progress updates
    - **Property 4: Progress Updates Emitted**
    - **Validates: Requirements 1.7**
    - Verify progress events are emitted after each sub-agent
    - Verify event order matches agent execution sequence
    - Run 100 iterations
    - _Requirements: 10.2_

  - [ ]* 10.6 Write property test for error handling
    - **Property 16: Error Handling Gracefully**
    - **Validates: Requirements 5.8**
    - Test network failures, timeouts, invalid responses
    - Verify system returns error without crashing
    - Verify error messages are helpful
    - Run 100 iterations
    - _Requirements: 10.2, 10.9_

  - [ ]* 10.7 Write property test for API compatibility
    - **Property 18: API Request Schema Compatibility**
    - **Property 19: API Response Format Compatibility**
    - **Validates: Requirements 15.1, 15.2**
    - Verify request schema unchanged from Strands implementation
    - Verify response format matches JSONLine structure
    - Run 100 iterations
    - _Requirements: 10.2, 15.1, 15.2_

  - [ ]* 10.8 Run all property tests and fix issues
    - Execute all property tests with 100 iterations each
    - Document any failures with counterexamples
    - Fix discovered issues
    - Re-run tests until all pass
    - _Requirements: 10.2_

- [ ] 11. Integration Phase - Week 3: Regression Testing (Both Developers)
  - Compare Bedrock output with Strands output
  - _Estimated time: 2 days_
  - _Requirements: 10.5, 13.1-13.5_

  - [ ] 11.1 Implement parallel comparison mode
    - Add COMPARE_IMPLEMENTATIONS environment variable
    - Implement invokeWithComparison function
    - Run both Strands and Bedrock implementations
    - Compare outputs and log differences
    - Store comparison results for analysis
    - _Requirements: 13.1, 13.2_

  - [ ] 11.2 Run 100 test proposals through both implementations
    - Create diverse test dataset covering various grant types
    - Include edge cases: early-career faculty, interdisciplinary grants, large faculty lists
    - Run both implementations for each test case
    - Collect outputs and metrics
    - _Requirements: 13.3_

  - [ ] 11.3 Analyze output similarity
    - Compare match scores (target: within ±5 points for 95% of cases)
    - Compare proposal draft lengths (target: within ±20% for 90% of cases)
    - Compare collaborator counts (target: exact match 100%)
    - Compare compliance checklist categories (target: exact match 100%)
    - Document discrepancies and investigate causes
    - _Requirements: 13.4_

  - [ ] 11.4 Measure performance comparison
    - Compare end-to-end latency (Bedrock vs Strands)
    - Measure P50, P95, P99 latencies
    - Verify Bedrock latency ≤ Strands latency + 5 seconds
    - Document performance results
    - _Requirements: 10.8, 15.10_

  - [ ] 11.5 Validate functional parity
    - Verify 95% functional parity across all metrics
    - Document any cases where Bedrock output differs significantly
    - Get stakeholder approval to proceed with migration
    - _Requirements: 13.5_

- [ ] 12. Checkpoint - Week 3 Mid: Validation Complete
  - Ensure all tests pass and functional parity is achieved
  - Ensure all tests pass, ask the user if questions arise

- [ ] 13. Migration Phase - Week 3-4: Deployment and Rollout (Both Developers)
  - Deploy to staging and production with gradual rollout
  - _Estimated time: 5 days_
  - _Requirements: 13.6-13.10, 9.1-9.9_

  - [ ] 13.1 Set up monitoring and observability
    - Create CloudWatch dashboards for agent metrics
    - Configure CloudWatch alarms for error rates and latency
    - Set up cost tracking with AWS Cost Explorer
    - Configure SNS notifications for alerts
    - Test alerting mechanisms
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 11.1-11.10_

  - [ ] 13.2 Deploy to staging environment
    - Deploy Express backend with Bedrock integration
    - Configure staging agent IDs and aliases
    - Run full test suite in staging
    - Verify monitoring and logging work correctly
    - _Requirements: 13.1_

  - [ ] 13.3 Test rollback procedure
    - Document rollback steps
    - Test immediate rollback (set traffic to 0%)
    - Verify Strands agents still work
    - Time rollback execution (target: < 15 minutes)
    - _Requirements: 13.6, 13.7, 13.8_

  - [ ] 13.4 Implement canary deployment (10% traffic)
    - Add BEDROCK_TRAFFIC_PERCENT environment variable
    - Implement traffic routing logic in Express backend
    - Deploy to production with 10% traffic to Bedrock
    - Monitor error rates, latency, and cost for 3 days
    - _Requirements: 13.1, 13.2_

  - [ ] 13.5 Gradual rollout to 50% traffic
    - Increase BEDROCK_TRAFFIC_PERCENT to 0.25 (25%)
    - Monitor for 2 days
    - Increase to 0.50 (50%)
    - Monitor for 2 days
    - Verify error rate and latency within acceptable thresholds
    - _Requirements: 13.1, 13.2_

  - [ ] 13.6 Gradual rollout to 100% traffic
    - Increase BEDROCK_TRAFFIC_PERCENT to 0.75 (75%)
    - Monitor for 2 days
    - Increase to 1.0 (100%)
    - Monitor for 5 days
    - Verify system stability
    - _Requirements: 13.1, 13.2_

  - [ ] 13.7 Validate migration success
    - Verify error rate < 1%
    - Verify P95 latency < 30 seconds
    - Verify cost within expected range ($220/month optimized)
    - Verify no critical user-reported issues
    - Get stakeholder approval for Strands deprecation
    - _Requirements: 13.5, 13.9_

- [ ] 14. Migration Phase - Week 4: Cleanup and Documentation (Both Developers)
  - Remove Strands code and finalize documentation
  - _Estimated time: 2 days_
  - _Requirements: 6.1-6.10, 14.1-14.10_

  - [ ] 14.1 Remove Strands agent code
    - Delete agent-service/agents/orchestrator.py
    - Delete agent-service/agents/sourcing.py
    - Delete agent-service/agents/matchmaking.py
    - Delete agent-service/agents/collaborator.py
    - Delete agent-service/agents/drafting.py
    - Delete agent-service/main.py
    - Delete agent-service/Dockerfile
    - Remove agent-service/ directory
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ] 14.2 Remove FastAPI service from deployment
    - Remove FastAPI service from docker-compose.yml
    - Remove AGENT_SERVICE_URL from production environment
    - Stop and remove FastAPI containers
    - _Requirements: 6.9_

  - [ ] 14.3 Archive Strands code for reference
    - Create git branch "archive/strands-implementation"
    - Push branch to remote repository
    - Document branch location in README
    - _Requirements: 6.10_

  - [ ] 14.4 Update all documentation
    - Update README with Bedrock Agents architecture
    - Update ARCHITECTURE.md with system diagrams
    - Document agent IDs and configuration
    - Document Knowledge Base setup and document management
    - Document Lambda Action Groups and OpenAPI schemas
    - Add troubleshooting guide
    - Document cost analysis and optimization
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9_

  - [ ] 14.5 Conduct team knowledge transfer
    - Present architecture overview to team
    - Walk through agent configuration and instructions
    - Demonstrate how to update agent instructions
    - Show how to add documents to Knowledge Base
    - Review monitoring dashboards and alerts
    - Review cost tracking and optimization
    - _Requirements: 14.10_

- [ ] 15. Final Checkpoint - Migration Complete
  - Verify all tasks complete and system is stable
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and provide sync points
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end functionality
- Regression tests ensure functional parity with Strands implementation
- Migration is phased with gradual rollout to minimize risk
- Rollback procedure is tested and documented for safety

## Timeline Summary

**Week 1:**
- Developer A: Bedrock Agents, Knowledge Base, IAM setup (Tasks 1.1-1.6)
- Developer B: Dependencies, AWS credentials, environment setup (Tasks 4.1-4.3)

**Week 2:**
- Developer A: Lambda Action Groups, agent integration testing (Tasks 2.1-3.4)
- Developer B: agent-client.ts refactoring, unit testing, cleanup (Tasks 5.1-7.3)

**Week 3:**
- Both: Integration testing, property-based testing, regression testing (Tasks 9.1-12)
- Both: Monitoring setup, staging deployment, canary deployment (Tasks 13.1-13.4)

**Week 4:**
- Both: Gradual rollout to 100%, validation (Tasks 13.5-13.7)
- Both: Cleanup, documentation, knowledge transfer (Tasks 14.1-14.5)

## Success Criteria

- All Bedrock Agents created and operational
- Knowledge Base retrieving relevant documents
- Lambda Action Groups integrated with agents
- Express backend using AWS SDK successfully
- All property tests passing (100 iterations each)
- 95% functional parity with Strands implementation
- Error rate < 1% in production
- P95 latency < 30 seconds
- Cost within expected range ($220/month optimized)
- No critical user-reported issues
- Complete documentation and team training
