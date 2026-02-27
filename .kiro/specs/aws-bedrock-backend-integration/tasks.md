# Implementation Plan: AWS Bedrock Backend Integration

## Overview

This implementation integrates AWS Bedrock's Claude 3 Haiku model into the FundingForge Express.js backend to replace mock proposal generation with real AI-powered streaming. The approach follows a modular architecture with three key components: a dedicated Bedrock client module, enhanced forge endpoint with SSE streaming, and environment validation at startup. All existing API contracts are preserved to ensure zero frontend changes are required.

## Tasks

- [ ] 1. Install dependencies and configure environment
  - Add @aws-sdk/client-bedrock-runtime package to dependencies
  - Add dotenv package to dependencies
  - Add fast-check package to devDependencies for property-based testing
  - Create .env.example file documenting required AWS environment variables
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 2. Implement environment validation module
  - [ ] 2.1 Create environment validator function in server/index.ts
    - Implement validateEnvironment() function that checks for DATABASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION
    - Log clear error messages identifying missing variables
    - Exit process with non-zero code if validation fails
    - Load dotenv in development mode before validation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 2.2 Write property test for environment validation
    - **Property 6: Environment validation failure handling**
    - **Validates: Requirements 3.5, 3.6**
  
  - [ ]* 2.3 Write unit tests for environment validator
    - Test each missing variable scenario (DATABASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    - Test development mode dotenv loading
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.7_

- [ ] 3. Create Bedrock client module
  - [ ] 3.1 Create server/bedrock.ts with ProposalParams interface and streamProposal function
    - Define ProposalParams interface with grantName, role, year, program, matchCriteria, eligibility fields
    - Implement streamProposal AsyncGenerator function
    - Configure BedrockRuntimeClient with AWS_REGION from environment
    - Use model ID: anthropic.claude-3-haiku-20240307-v1:0
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_
  
  - [ ] 3.2 Implement system prompt and user message construction
    - Create system prompt identifying AI as FSU grant writing assistant
    - Build user message template incorporating all ProposalParams
    - Configure model parameters (max tokens: 4096, temperature: 0.7, top P: 0.9)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 3.3 Implement stream processing logic
    - Invoke InvokeModelWithResponseStreamCommand
    - Iterate over response stream chunks
    - Decode chunk bytes and extract contentBlockDelta text tokens
    - Yield each text token as string
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ] 3.4 Implement AWS error handling
    - Catch AccessDeniedException and throw descriptive error
    - Catch ThrottlingException and throw descriptive error
    - Handle empty stream body with descriptive error
    - Throw descriptive errors for other AWS exceptions
    - _Requirements: 1.7, 1.8, 1.9_
  
  - [ ]* 3.5 Write property test for system prompt inclusion
    - **Property 9: System prompt inclusion**
    - **Validates: Requirements 7.1**
  
  - [ ]* 3.6 Write property test for parameter incorporation
    - **Property 10: Parameter incorporation in user message**
    - **Validates: Requirements 7.4, 7.5**
  
  - [ ]* 3.7 Write property test for stream round-trip integrity
    - **Property 8: Stream processing round-trip integrity**
    - **Validates: Requirements 6.6**
  
  - [ ]* 3.8 Write unit tests for Bedrock client
    - Test correct model ID is used
    - Test system prompt is included in requests
    - Test AWS region from environment is used
    - Test AccessDeniedException throws descriptive error
    - Test ThrottlingException throws descriptive error
    - Test empty stream throws descriptive error
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8, 1.9, 7.1_

- [ ] 4. Checkpoint - Ensure Bedrock client module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Update forge endpoint with Bedrock integration
  - [ ] 5.1 Import Bedrock client and update /api/forge/:grantId endpoint in server/routes.ts
    - Import streamProposal from server/bedrock.ts
    - Extract grantId from URL path parameters
    - Extract role, year, program from query parameters
    - Retrieve grant record from storage using grantId
    - Handle grant not found scenario with error SSE message
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 5.2 Implement status step messages before streaming
    - Send exactly 3 status messages via SSE before invoking Bedrock
    - Use messages: "Sourcing Agent is checking FSU internal policies...", "Analyzing applicant history and match criteria...", "Drafting proposal summary based on previous successful grants..."
    - Add 500ms delay between status messages
    - _Requirements: 2.4_
  
  - [ ] 5.3 Implement token streaming loop
    - Call streamProposal with all ProposalParams (grantName, role, year, program, matchCriteria, eligibility)
    - For each token yielded, send SSE message: { step: "streaming", done: false, token: string }
    - Collect all tokens in array for final concatenation
    - _Requirements: 2.5, 2.8, 2.9_
  
  - [ ] 5.4 Implement completion and error handling
    - Send completion message with concatenated proposal: { step: "Complete", done: true, result: { proposal: string } }
    - Implement error sanitization function to map AWS errors to user-friendly messages
    - Send error SSE message on exceptions: { step: error message, done: true, error: true }
    - Map AccessDeniedException to "service unavailable" message
    - Map ThrottlingException to "high demand" message
    - _Requirements: 2.6, 2.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 5.5 Write property test for grant retrieval
    - **Property 1: Grant retrieval for valid requests**
    - **Validates: Requirements 2.3**
  
  - [ ]* 5.6 Write property test for token streaming format
    - **Property 2: Token streaming format preservation**
    - **Validates: Requirements 2.5**
  
  - [ ]* 5.7 Write property test for stream completion
    - **Property 3: Stream completion message**
    - **Validates: Requirements 2.6**
  
  - [ ]* 5.8 Write property test for parameter forwarding
    - **Property 4: Parameter forwarding to Bedrock**
    - **Validates: Requirements 2.8, 2.9**
  
  - [ ]* 5.9 Write property test for SSE format compatibility
    - **Property 5: SSE message format compatibility**
    - **Validates: Requirements 2.10**
  
  - [ ]* 5.10 Write property test for AWS error sanitization
    - **Property 7: AWS error sanitization**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  
  - [ ]* 5.11 Write unit tests for forge endpoint
    - Test exactly 3 status messages sent before streaming
    - Test error during streaming sends error message
    - Test AccessDeniedException mapped to "service unavailable"
    - Test ThrottlingException mapped to "high demand" message
    - _Requirements: 2.4, 2.7, 4.5, 4.6_

- [ ] 6. Checkpoint - Ensure forge endpoint tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Verify API contract preservation
  - [ ]* 7.1 Write integration tests for existing endpoints
    - Test GET /api/grants returns Grant[] array
    - Test GET /api/faculty returns Faculty[] array
    - Test GET /api/forge/:grantId uses SSE streaming interface
    - Test seeding logic still works correctly
    - _Requirements: 5.1, 5.2, 5.3, 5.6_
  
  - [ ] 7.2 Verify no changes to shared schema or client code
    - Confirm shared/schema.ts is unchanged
    - Confirm no files in client/ directory are modified
    - _Requirements: 5.4, 5.5_

- [ ] 8. Create documentation
  - [ ] 8.1 Update README with AWS setup instructions
    - Document required AWS environment variables
    - Provide example .env configuration
    - Document required IAM permissions for Bedrock access
    - Include cost considerations and monitoring recommendations
    - _Requirements: 8.3_
  
  - [ ] 8.2 Add inline code documentation
    - Add JSDoc comments to ProposalParams interface
    - Add JSDoc comments to streamProposal function
    - Add JSDoc comments to validateEnvironment function
    - Document error handling strategy in comments
    - _Requirements: 1.3, 1.7, 1.8, 1.9_

- [ ] 9. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests use fast-check library with minimum 100 iterations
- All AWS errors must be sanitized before sending to clients
- The implementation preserves all existing API contracts for zero frontend changes
- Environment validation runs at server startup to catch configuration issues early
