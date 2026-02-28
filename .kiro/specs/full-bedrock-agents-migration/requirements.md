# Requirements Document: Full Bedrock Agents Migration

## Introduction

This document specifies requirements for migrating FundingForge from the current Strands Agents + FastAPI architecture to a full AWS Bedrock Agents implementation (Option 3 from AWS_INTEGRATION_ANALYSIS.md). The migration replaces custom agent orchestration with AWS-managed multi-agent collaboration, integrates Knowledge Base for Amazon Bedrock for RAG capabilities, and updates the Express backend to use native AWS SDK APIs.

The implementation will be split between 2 developers working in parallel to minimize timeline while maintaining system stability.

## Glossary

- **Bedrock_Agent**: An AWS-managed AI agent that uses foundation models and can be configured with instructions, action groups, and knowledge bases
- **Supervisor_Agent**: The top-level Bedrock Agent that orchestrates sub-agents and manages the overall proposal generation workflow
- **Sub_Agent**: A specialized Bedrock Agent (Sourcing, Matchmaking, Collaborator, or Drafting) invoked by the Supervisor Agent
- **Action_Group**: A Lambda function that provides custom logic to a Bedrock Agent via OpenAPI schema
- **Knowledge_Base**: AWS service that provides RAG capabilities by connecting to S3 data sources and performing vector search
- **InvokeAgent_API**: AWS SDK API for invoking Bedrock Agents and receiving streaming responses
- **Session_State**: Bedrock Agent session context that maintains conversation history and attributes across invocations
- **Agent_Alias**: A versioned deployment of a Bedrock Agent (e.g., DRAFT, PROD)
- **Express_Backend**: The Node.js/TypeScript server that handles HTTP requests and invokes agents
- **SSE_Stream**: Server-Sent Events stream that delivers real-time updates to the frontend
- **JSON_Line**: Newline-delimited JSON format used for streaming agent responses
- **Strands_Agent**: The current custom agent implementation using the Strands SDK (to be replaced)
- **FastAPI_Service**: The current Python service hosting Strands Agents (to be removed)
- **Orchestrator_Agent**: The current custom agent that coordinates execution flow (to be replaced by Supervisor Agent)
- **Vector_Store**: OpenSearch Serverless collection that stores document embeddings for semantic search
- **Ingestion_Job**: AWS process that converts S3 documents into embeddings and stores them in the Vector Store
- **CloudWatch_Logs**: AWS logging service for monitoring agent execution and debugging
- **IAM_Role**: AWS identity with permissions for agents to access other AWS services
- **boto3**: Python AWS SDK (used in Lambda functions)
- **AWS_SDK**: JavaScript/TypeScript AWS SDK (used in Express backend)

## Requirements

### Requirement 1: Bedrock Supervisor Agent Creation

**User Story:** As a system architect, I want to create a Supervisor Agent in Amazon Bedrock, so that I can orchestrate the multi-agent proposal generation workflow using AWS-managed services.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL be created in Amazon Bedrock with a unique agent ID and DRAFT alias
2. THE Supervisor_Agent SHALL be configured with foundation model Claude 3.5 Sonnet
3. THE Supervisor_Agent SHALL have instructions that define its role as orchestrator of the proposal generation pipeline
4. THE Supervisor_Agent SHALL be configured to invoke four Sub_Agents in sequence: Sourcing, Matchmaking, Collaborator, and Drafting
5. THE Supervisor_Agent SHALL aggregate outputs from all Sub_Agents into a final result payload containing proposalDraft, collaborators, matchScore, matchJustification, and complianceChecklist
6. THE Supervisor_Agent SHALL maintain Session_State across sub-agent invocations to preserve context
7. THE Supervisor_Agent SHALL emit progress updates at each orchestration step
8. THE Supervisor_Agent SHALL have an IAM_Role with permissions to invoke Sub_Agents

### Requirement 2: Bedrock Sub-Agent Creation

**User Story:** As a system architect, I want to create four specialized Sub_Agents in Amazon Bedrock, so that each agent can focus on a specific aspect of proposal generation.

#### Acceptance Criteria

1. THE Sourcing_Sub_Agent SHALL be created with instructions to extract user experience and expertise from the user profile
2. THE Matchmaking_Sub_Agent SHALL be created with instructions to analyze grant match criteria and generate compliance checklists
3. THE Collaborator_Sub_Agent SHALL be created with instructions to identify and rank potential faculty collaborators
4. THE Drafting_Sub_Agent SHALL be created with instructions to generate proposal drafts based on grant requirements
5. WHEN a Sub_Agent is invoked, THE Sub_Agent SHALL receive input parameters from the Supervisor_Agent via Session_State
6. WHEN a Sub_Agent completes execution, THE Sub_Agent SHALL return structured output to the Supervisor_Agent
7. THE Matchmaking_Sub_Agent SHALL be linked to the Knowledge_Base for retrieving compliance documents
8. FOR ALL Sub_Agents, THE Sub_Agent SHALL use foundation model Claude 3.5 Sonnet

### Requirement 3: Knowledge Base Setup with S3

**User Story:** As a system architect, I want to create a Knowledge Base connected to S3, so that agents can retrieve grant policies, templates, and compliance documents using RAG.

#### Acceptance Criteria

1. THE Knowledge_Base SHALL be created in Amazon Bedrock with name "FundingForgeKnowledgeBase"
2. THE Knowledge_Base SHALL use Amazon Titan Embed Text v2 as the embedding model
3. THE Knowledge_Base SHALL be configured with OpenSearch Serverless as the Vector_Store
4. THE S3_Bucket "fundingforge-knowledge-base" SHALL be created to store grant documents
5. THE S3_Bucket SHALL contain three prefixes: policies/, templates/, and compliance/
6. THE Knowledge_Base SHALL have a data source configured to sync from the S3_Bucket
7. WHEN documents are uploaded to S3, THE Ingestion_Job SHALL convert them to embeddings and store in the Vector_Store
8. THE Matchmaking_Sub_Agent SHALL be configured to retrieve up to 10 documents from the Knowledge_Base using hybrid search
9. THE Knowledge_Base SHALL have an IAM_Role with permissions to read from S3 and write to OpenSearch Serverless

### Requirement 4: Action Groups for Custom Logic

**User Story:** As a developer, I want to create Lambda-based Action Groups, so that Bedrock Agents can execute custom business logic that cannot be expressed in prompts alone.

#### Acceptance Criteria

1. THE Faculty_Ranking_Action_Group SHALL be created as a Lambda function that ranks faculty by expertise match
2. THE Compliance_Checker_Action_Group SHALL be created as a Lambda function that validates compliance checklist items
3. THE Proposal_Formatter_Action_Group SHALL be created as a Lambda function that formats proposal drafts according to grant templates
4. WHEN an Action_Group is invoked by a Bedrock_Agent, THE Action_Group SHALL receive parameters via the Lambda event
5. WHEN an Action_Group completes, THE Action_Group SHALL return structured JSON response to the Bedrock_Agent
6. THE Action_Groups SHALL be defined with OpenAPI 3.0 schemas that specify input parameters and response formats
7. THE Collaborator_Sub_Agent SHALL be configured to use the Faculty_Ranking_Action_Group
8. THE Matchmaking_Sub_Agent SHALL be configured to use the Compliance_Checker_Action_Group
9. THE Drafting_Sub_Agent SHALL be configured to use the Proposal_Formatter_Action_Group
10. FOR ALL Action_Groups, THE Action_Group SHALL have an IAM_Role with necessary permissions for its operations

### Requirement 5: Express Backend Migration to AWS SDK

**User Story:** As a backend developer, I want to replace HTTP calls to FastAPI with AWS SDK InvokeAgent API calls, so that the Express backend communicates directly with Bedrock Agents.

#### Acceptance Criteria

1. THE Express_Backend SHALL install @aws-sdk/client-bedrock-agent-runtime package
2. THE agent-client.ts file SHALL be refactored to use BedrockAgentRuntimeClient instead of fetch
3. WHEN invokeAgentPipeline is called, THE Express_Backend SHALL invoke the Supervisor_Agent using InvokeAgentCommand
4. THE Express_Backend SHALL pass grantId, grantName, matchCriteria, eligibility, userProfile, and facultyList as session attributes
5. WHEN the Supervisor_Agent returns a streaming response, THE Express_Backend SHALL parse the completion stream
6. THE Express_Backend SHALL convert Bedrock Agent events to JSON_Line format for compatibility with existing SSE implementation
7. THE Express_Backend SHALL enable trace logging for observability by setting enableTrace: true
8. THE Express_Backend SHALL handle agent errors gracefully and return appropriate error messages to the frontend
9. THE Express_Backend SHALL maintain the same AsyncGenerator<JSONLine> interface to avoid frontend changes
10. THE Express_Backend SHALL read AWS credentials from environment variables or IAM role

### Requirement 6: Remove Custom Orchestration Code

**User Story:** As a developer, I want to remove the custom Strands orchestration code, so that the system relies entirely on Bedrock's built-in multi-agent orchestration.

#### Acceptance Criteria

1. THE agent-service/agents/orchestrator.py file SHALL be deleted
2. THE agent-service/agents/sourcing.py file SHALL be deleted
3. THE agent-service/agents/matchmaking.py file SHALL be deleted
4. THE agent-service/agents/collaborator.py file SHALL be deleted
5. THE agent-service/agents/drafting.py file SHALL be deleted
6. THE agent-service/main.py FastAPI application SHALL be deleted
7. THE agent-service/Dockerfile SHALL be deleted
8. THE AGENT_SERVICE_URL environment variable SHALL be removed from Express configuration
9. THE Express_Backend SHALL no longer make HTTP calls to port 8001
10. THE deployment documentation SHALL be updated to reflect removal of the FastAPI service

### Requirement 7: Local Development and Testing Support

**User Story:** As a developer, I want to test Bedrock Agents locally, so that I can develop and debug without deploying to AWS on every change.

#### Acceptance Criteria

1. THE development environment SHALL support AWS credentials via environment variables or AWS CLI profiles
2. THE Express_Backend SHALL support a LOCAL_MODE environment variable that uses a test Bedrock Agent alias
3. WHEN running locally, THE Express_Backend SHALL log all InvokeAgent requests and responses for debugging
4. THE Action_Group Lambda functions SHALL be testable locally using AWS SAM CLI or similar tools
5. THE Knowledge_Base SHALL support manual ingestion triggers for testing document updates
6. THE development documentation SHALL include instructions for setting up AWS credentials locally
7. THE development documentation SHALL include instructions for creating test agents in a development AWS account
8. WHEN a developer modifies agent instructions, THE developer SHALL be able to update the DRAFT alias without affecting production

### Requirement 8: Parallel Work Breakdown for 2 Developers

**User Story:** As a project manager, I want to split the migration work between 2 developers, so that the implementation can be completed in parallel to minimize timeline.

#### Acceptance Criteria

1. THE work SHALL be divided into two parallel tracks: AWS Infrastructure (Developer A) and Express Backend (Developer B)
2. THE AWS Infrastructure track SHALL include: creating Bedrock Agents, Knowledge Base setup, Lambda Action Groups, and IAM roles
3. THE Express Backend track SHALL include: refactoring agent-client.ts, updating environment configuration, and removing FastAPI dependencies
4. THE two tracks SHALL have a clear integration point after 1 week where Developer B can test against Developer A's deployed agents
5. THE AWS Infrastructure track SHALL be estimated at 8-10 days for a single developer
6. THE Express Backend track SHALL be estimated at 5-7 days for a single developer
7. THE integration and testing phase SHALL be estimated at 3-4 days with both developers
8. THE total timeline SHALL be 2-3 weeks with 2 developers working in parallel
9. THE work breakdown SHALL include daily sync points to ensure alignment between tracks

### Requirement 9: Cost Monitoring and Optimization

**User Story:** As a system administrator, I want to monitor and optimize AWS costs, so that the Bedrock Agents implementation remains cost-effective.

#### Acceptance Criteria

1. THE system SHALL use AWS Cost Explorer to track Bedrock Agent invocation costs
2. THE system SHALL use AWS Cost Explorer to track Knowledge Base retrieval costs
3. THE system SHALL use AWS Cost Explorer to track foundation model inference costs
4. THE system SHALL log the number of tokens used per agent invocation in CloudWatch_Logs
5. THE system SHALL set up CloudWatch alarms for daily cost thresholds exceeding $50
6. THE Matchmaking_Sub_Agent SHALL limit Knowledge_Base retrievals to 10 documents per invocation to control costs
7. THE Supervisor_Agent SHALL use caching where possible to reduce redundant model invocations
8. THE system SHALL generate monthly cost reports comparing actual costs to the estimated $120/month for 1000 proposals
9. WHEN costs exceed budget, THE system administrator SHALL receive email notifications via SNS

### Requirement 10: Testing Strategy for Bedrock Agents

**User Story:** As a QA engineer, I want a comprehensive testing strategy for Bedrock Agents, so that I can verify the migration maintains functional parity with the Strands implementation.

#### Acceptance Criteria

1. THE testing strategy SHALL include unit tests for Lambda Action Groups using Jest or pytest
2. THE testing strategy SHALL include integration tests that invoke the Supervisor_Agent with sample payloads
3. THE testing strategy SHALL include end-to-end tests that verify the complete pipeline from Express to frontend
4. THE testing strategy SHALL include Knowledge Base retrieval tests that verify relevant documents are returned
5. THE testing strategy SHALL include regression tests comparing outputs from Strands agents vs Bedrock Agents
6. WHEN an integration test is run, THE test SHALL verify that all four Sub_Agents are invoked in the correct sequence
7. WHEN an integration test is run, THE test SHALL verify that the final output contains all required fields: proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
8. THE testing strategy SHALL include performance tests measuring end-to-end latency (target: under 30 seconds)
9. THE testing strategy SHALL include error handling tests for network failures, timeout scenarios, and invalid inputs
10. THE testing strategy SHALL include a rollback plan to revert to Strands agents if critical issues are discovered

### Requirement 11: Observability and Debugging

**User Story:** As a developer, I want comprehensive observability for Bedrock Agents, so that I can debug issues and monitor system health in production.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL enable trace logging to CloudWatch_Logs
2. THE Sub_Agents SHALL enable trace logging to CloudWatch_Logs
3. WHEN an agent is invoked, THE system SHALL log the session ID, input parameters, and timestamp
4. WHEN an agent completes, THE system SHALL log the output, token count, and execution duration
5. WHEN an agent encounters an error, THE system SHALL log the error message, stack trace, and input that caused the failure
6. THE CloudWatch_Logs SHALL be organized into log groups per agent for easy filtering
7. THE system SHALL create CloudWatch dashboards showing agent invocation counts, error rates, and latency percentiles
8. THE system SHALL set up CloudWatch alarms for error rates exceeding 5%
9. THE Express_Backend SHALL log correlation IDs that link frontend requests to Bedrock Agent invocations
10. THE system SHALL retain logs for 30 days for debugging and compliance purposes

### Requirement 12: Security and IAM Configuration

**User Story:** As a security engineer, I want proper IAM roles and policies configured, so that Bedrock Agents follow the principle of least privilege.

#### Acceptance Criteria

1. THE Supervisor_Agent SHALL have an IAM_Role with permissions to invoke Sub_Agents only
2. THE Sub_Agents SHALL have IAM_Roles with permissions to invoke foundation models and their assigned Action_Groups only
3. THE Matchmaking_Sub_Agent IAM_Role SHALL include permissions to retrieve from the Knowledge_Base
4. THE Knowledge_Base SHALL have an IAM_Role with permissions to read from S3 and write to OpenSearch Serverless only
5. THE Action_Group Lambda functions SHALL have IAM_Roles with permissions for their specific operations only
6. THE Express_Backend SHALL use an IAM_Role (in production) or IAM user credentials (in development) to invoke the Supervisor_Agent
7. THE S3_Bucket SHALL have encryption at rest enabled using AWS KMS
8. THE OpenSearch Serverless collection SHALL have encryption at rest enabled
9. THE Bedrock Agent invocations SHALL use TLS 1.2 or higher for data in transit
10. THE IAM policies SHALL be reviewed and approved by the security team before production deployment

### Requirement 13: Migration Validation and Rollback

**User Story:** As a project manager, I want a validation process and rollback plan, so that we can safely migrate to Bedrock Agents without risking production stability.

#### Acceptance Criteria

1. THE migration SHALL include a validation phase where both Strands and Bedrock implementations run in parallel
2. WHEN running in parallel mode, THE system SHALL invoke both implementations and compare outputs
3. THE validation phase SHALL run for at least 100 test proposals covering diverse grant types and user profiles
4. THE validation SHALL measure output similarity using automated comparison of proposalDraft, matchScore, and complianceChecklist fields
5. THE validation SHALL require 95% functional parity before proceeding to full cutover
6. THE rollback plan SHALL include reverting Express backend to use HTTP calls to FastAPI
7. THE rollback plan SHALL include redeploying the FastAPI service from the previous Docker image
8. THE rollback plan SHALL be executable within 15 minutes in case of critical production issues
9. THE migration SHALL use feature flags to toggle between Strands and Bedrock implementations
10. THE migration SHALL be communicated to users with a maintenance window notification

### Requirement 14: Documentation and Knowledge Transfer

**User Story:** As a team member, I want comprehensive documentation for the Bedrock Agents implementation, so that I can maintain and extend the system after migration.

#### Acceptance Criteria

1. THE documentation SHALL include an architecture diagram showing Supervisor Agent, Sub-Agents, Knowledge Base, and Action Groups
2. THE documentation SHALL include step-by-step instructions for creating and configuring each Bedrock Agent
3. THE documentation SHALL include OpenAPI schemas for all Action Groups
4. THE documentation SHALL include instructions for updating agent instructions and deploying new aliases
5. THE documentation SHALL include instructions for adding new documents to the Knowledge Base
6. THE documentation SHALL include troubleshooting guides for common issues (e.g., permission errors, timeout errors)
7. THE documentation SHALL include cost analysis and optimization recommendations
8. THE documentation SHALL include instructions for monitoring agent performance using CloudWatch
9. THE documentation SHALL include code examples for invoking agents from Express backend
10. THE documentation SHALL be reviewed and approved by at least 2 team members before migration completion

### Requirement 15: Frontend Compatibility

**User Story:** As a frontend developer, I want the Express backend API to remain unchanged, so that I don't need to modify the frontend during the Bedrock migration.

#### Acceptance Criteria

1. THE Express_Backend /api/invoke endpoint SHALL maintain the same request schema after migration
2. THE Express_Backend /api/invoke endpoint SHALL maintain the same response schema (JSON_Line format) after migration
3. THE SSE_Stream SHALL continue to emit events with the same structure: agent, step, output, done
4. THE final completion event SHALL contain the same fields: proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist
5. THE error responses SHALL maintain the same HTTP status codes and error message formats
6. WHEN the frontend invokes /api/invoke, THE frontend SHALL receive real-time progress updates as before
7. THE migration SHALL not require any changes to frontend TypeScript interfaces
8. THE migration SHALL not require any changes to frontend React components
9. THE migration SHALL be transparent to end users (no UI changes)
10. THE migration SHALL maintain the same end-to-end latency (target: under 30 seconds for complete pipeline)
