# Requirements Document

## Introduction

This feature integrates AWS Bedrock's Claude 4.6 Sonnet and 4.5 Haiku models into the FundingForge Express.js backend to replace mock proposal generation with real AI-powered grant writing assistance. The integration must preserve all existing API contracts while adding production-ready AI capabilities through server-sent events (SSE) streaming.

## Glossary

- **Bedrock_Client**: AWS Bedrock Runtime client that invokes foundation models
- **Forge_Endpoint**: The /api/forge/:grantId SSE endpoint that streams proposal generation
- **Profile_Parameters**: Query parameters (role, year, program) that define the faculty member's context
- **Grant_Record**: Database record containing grant details retrieved by grantId
- **Proposal_Stream**: AsyncGenerator that yields AI-generated proposal text tokens
- **Status_Step**: SSE message indicating current processing phase
- **Environment_Validator**: Startup module that verifies required configuration variables

## Requirements

### Requirement 1: Bedrock Client Module

**User Story:** As a backend developer, I want a dedicated Bedrock integration module, so that AI model invocation is encapsulated and reusable.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL use BedrockRuntimeClient from @aws-sdk/client-bedrock-runtime
2. THE Bedrock_Client SHALL invoke model anthropic.claude-3-haiku-20240307-v1:0
3. THE Bedrock_Client SHALL expose a streamProposal function that returns an AsyncGenerator<string>
4. WHEN streamProposal is called, THE Bedrock_Client SHALL accept parameters: grantName, role, year, program, matchCriteria, and eligibility
5. THE Bedrock_Client SHALL include a system prompt defining an FSU grant writing assistant persona
6. WHEN AWS_REGION is set, THE Bedrock_Client SHALL use that region for API calls
7. IF AccessDeniedException occurs, THEN THE Bedrock_Client SHALL throw a descriptive error
8. IF throttling occurs, THEN THE Bedrock_Client SHALL throw a descriptive error
9. IF the response stream body is empty, THEN THE Bedrock_Client SHALL throw a descriptive error

### Requirement 2: Forge Endpoint Integration

**User Story:** As a frontend developer, I want the /api/forge/:grantId endpoint to stream real AI proposals, so that users receive authentic grant writing assistance.

#### Acceptance Criteria

1. WHEN a request is received, THE Forge_Endpoint SHALL extract grantId from the URL path
2. WHEN a request is received, THE Forge_Endpoint SHALL extract role, year, and program from query parameters
3. THE Forge_Endpoint SHALL retrieve the Grant_Record from storage using grantId
4. THE Forge_Endpoint SHALL send 3 Status_Step messages via SSE before invoking Bedrock_Client
5. WHEN Bedrock_Client returns tokens, THE Forge_Endpoint SHALL send each token as: { step: "streaming", done: false, token: string }
6. WHEN the Proposal_Stream completes, THE Forge_Endpoint SHALL send: { step: "Complete", done: true, result: { proposal: string } }
7. IF an error occurs during streaming, THEN THE Forge_Endpoint SHALL send: { step: error message, done: true, error: true }
8. THE Forge_Endpoint SHALL pass Profile_Parameters to streamProposal
9. THE Forge_Endpoint SHALL pass Grant_Record details to streamProposal
10. THE Forge_Endpoint SHALL preserve the existing SSE response format

### Requirement 3: Environment Configuration Validation

**User Story:** As a DevOps engineer, I want the server to validate AWS credentials on startup, so that configuration issues are detected before serving requests.

#### Acceptance Criteria

1. WHEN the server starts, THE Environment_Validator SHALL check that DATABASE_URL is set
2. WHEN the server starts, THE Environment_Validator SHALL check that AWS_ACCESS_KEY_ID is set
3. WHEN the server starts, THE Environment_Validator SHALL check that AWS_SECRET_ACCESS_KEY is set
4. WHEN the server starts, THE Environment_Validator SHALL check that AWS_REGION is set
5. IF any required variable is missing, THEN THE Environment_Validator SHALL log a clear error message
6. IF any required variable is missing, THEN THE Environment_Validator SHALL exit the process
7. WHERE the environment is development, THE Environment_Validator SHALL load dotenv before validation

### Requirement 4: Error Handling and Security

**User Story:** As a security engineer, I want AWS errors to be sanitized before sending to clients, so that sensitive infrastructure details are not exposed.

#### Acceptance Criteria

1. WHEN a Bedrock error occurs, THE Forge_Endpoint SHALL map it to a user-friendly message
2. THE Forge_Endpoint SHALL NOT expose raw AWS error details in SSE messages
3. THE Forge_Endpoint SHALL NOT expose AWS credentials in error messages
4. THE Forge_Endpoint SHALL NOT expose internal service names in error messages
5. WHEN AccessDeniedException occurs, THE Forge_Endpoint SHALL send a generic "service unavailable" message
6. WHEN throttling occurs, THE Forge_Endpoint SHALL send a "high demand" message

### Requirement 5: API Contract Preservation

**User Story:** As a frontend developer, I want existing API endpoints to remain unchanged, so that the frontend continues to function without modifications.

#### Acceptance Criteria

1. THE Backend SHALL preserve GET /api/grants returning Grant[]
2. THE Backend SHALL preserve GET /api/faculty returning Faculty[]
3. THE Backend SHALL preserve GET /api/forge/:grantId SSE streaming interface
4. THE Backend SHALL NOT modify shared/schema.ts
5. THE Backend SHALL NOT modify any files in client/ directory
6. THE Backend SHALL preserve the existing seeding logic in routes.ts

### Requirement 6: Bedrock Stream Processing

**User Story:** As a backend developer, I want to correctly process Bedrock's streaming response format, so that proposal text is extracted and forwarded to the client.

#### Acceptance Criteria

1. WHEN Bedrock returns a stream, THE Proposal_Stream SHALL decode each chunk
2. WHEN a chunk contains a content block delta, THE Proposal_Stream SHALL extract the text token
3. THE Proposal_Stream SHALL yield each text token as a string
4. WHEN the stream ends, THE Proposal_Stream SHALL complete the AsyncGenerator
5. IF the stream contains no content blocks, THEN THE Proposal_Stream SHALL throw an error
6. FOR ALL valid proposal requests, streaming then concatenating tokens SHALL produce a complete proposal (round-trip property)

### Requirement 7: System Prompt Configuration

**User Story:** As a product manager, I want the AI to present itself as an FSU grant writing assistant, so that generated proposals align with institutional context.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL include a system prompt in every model invocation
2. THE system prompt SHALL identify the AI as an FSU grant writing assistant
3. THE system prompt SHALL instruct the model to generate grant proposals
4. THE system prompt SHALL reference the provided grant criteria and faculty profile
5. WHEN Profile_Parameters change, THE Bedrock_Client SHALL incorporate them into the user message

### Requirement 8: Dependency Management

**User Story:** As a backend developer, I want to know which npm packages are required, so that I can install dependencies correctly.

#### Acceptance Criteria

1. THE Backend SHALL require @aws-sdk/client-bedrock-runtime package
2. THE Backend SHALL require dotenv package for development
3. THE Backend SHALL document all new package dependencies
4. THE Backend SHALL NOT add packages beyond AWS SDK and dotenv
