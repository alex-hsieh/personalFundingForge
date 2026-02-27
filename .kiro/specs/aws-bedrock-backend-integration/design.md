# Design Document: AWS Bedrock Backend Integration

## Overview

This design integrates AWS Bedrock's Claude 3 Haiku model into the FundingForge Express.js backend to replace mock proposal generation with real AI-powered grant writing assistance. The integration maintains backward compatibility with existing API contracts while introducing production-ready streaming capabilities through Server-Sent Events (SSE).

The architecture follows a modular approach with three key components:
1. **Bedrock Client Module** (`server/bedrock.ts`) - Encapsulates AWS SDK interactions and streaming logic
2. **Enhanced Forge Endpoint** (`server/routes.ts`) - Orchestrates the proposal generation flow with SSE
3. **Environment Validator** (`server/index.ts`) - Ensures required AWS credentials are present at startup

The design prioritizes security by sanitizing AWS errors before exposing them to clients, and maintains the existing SSE message format to ensure zero frontend changes are required.

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    Client[Frontend Client]
    Express[Express Server]
    Validator[Environment Validator]
    Routes[Routes Module]
    Bedrock[Bedrock Client Module]
    Storage[Storage Layer]
    AWS[AWS Bedrock Service]
    DB[(PostgreSQL)]

    Client -->|SSE Request| Express
    Express -->|Startup| Validator
    Validator -->|Check Env Vars| Express
    Express -->|Register Routes| Routes
    Routes -->|Stream Proposal| Bedrock
    Routes -->|Get Grant| Storage
    Storage -->|Query| DB
    Bedrock -->|Invoke Model| AWS
    AWS -->|Stream Tokens| Bedrock
    Bedrock -->|Yield Tokens| Routes
    Routes -->|SSE Messages| Client
```

### Request Flow Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Routes
    participant S as Storage
    participant B as Bedrock Client
    participant AWS as AWS Bedrock

    C->>R: GET /api/forge/:grantId?role=X&year=Y&program=Z
    R->>R: Extract grantId and query params
    R->>S: getGrants() - find by grantId
    S-->>R: Grant record
    R->>C: SSE: "Sourcing Agent checking policies..."
    R->>C: SSE: "Analyzing applicant history..."
    R->>C: SSE: "Drafting proposal summary..."
    R->>B: streamProposal(grantName, role, year, program, ...)
    B->>AWS: InvokeModelWithResponseStream
    loop For each token
        AWS-->>B: Stream chunk with content delta
        B->>B: Decode and extract text token
        B-->>R: Yield token string
        R->>C: SSE: {step: "streaming", done: false, token: "..."}
    end
    AWS-->>B: Stream complete
    B-->>R: AsyncGenerator complete
    R->>R: Concatenate all tokens
    R->>C: SSE: {step: "Complete", done: true, result: {proposal: "..."}}
```

## Components and Interfaces

### 1. Bedrock Client Module (`server/bedrock.ts`)

This module encapsulates all AWS Bedrock interactions and provides a clean streaming interface.

#### Interface Definition

```typescript
/**
 * Parameters for generating a grant proposal
 */
export interface ProposalParams {
  grantName: string;
  role: string;
  year: string;
  program: string;
  matchCriteria: string;
  eligibility: string;
}

/**
 * Streams a grant proposal from AWS Bedrock Claude 3 Haiku
 * @param params - Faculty profile and grant details
 * @returns AsyncGenerator yielding text tokens
 * @throws Error if AWS credentials are invalid or service is unavailable
 */
export async function* streamProposal(
  params: ProposalParams
): AsyncGenerator<string, void, unknown>;
```

#### Implementation Details

**AWS SDK Configuration:**
- Uses `BedrockRuntimeClient` from `@aws-sdk/client-bedrock-runtime`
- Reads region from `AWS_REGION` environment variable
- Credentials automatically loaded from environment (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

**Model Configuration:**
- Model ID: `anthropic.claude-3-haiku-20240307-v1:0`
- Max tokens: 4096
- Temperature: 0.7 (balanced creativity and consistency)
- Top P: 0.9

**System Prompt:**
```
You are an FSU grant writing assistant. Your role is to help faculty members 
draft compelling grant proposals based on their profile and the grant's requirements.

Generate a professional grant proposal that:
- Addresses the specific match criteria and eligibility requirements
- Incorporates the faculty member's role, year, and program context
- Follows standard grant proposal structure (introduction, objectives, methodology, impact)
- Uses clear, persuasive academic language
- Stays within typical proposal length guidelines
```

**User Message Template:**
```
Generate a grant proposal for the following:

Grant: {grantName}
Faculty Role: {role}
Academic Year: {year}
Program: {program}
Match Criteria: {matchCriteria}
Eligibility: {eligibility}

Please provide a complete proposal draft.
```

**Stream Processing Logic:**
1. Construct request payload with system prompt and user message
2. Invoke `InvokeModelWithResponseStreamCommand`
3. Iterate over response stream chunks
4. For each chunk:
   - Decode the chunk bytes to JSON
   - Check for `contentBlockDelta` event type
   - Extract `delta.text` field
   - Yield the text token
5. Handle stream completion
6. Throw descriptive errors for AWS exceptions

**Error Handling:**
- `AccessDeniedException` → "AWS Bedrock access denied. Please check credentials."
- `ThrottlingException` → "AWS Bedrock service is experiencing high demand. Please try again."
- Empty stream body → "AWS Bedrock returned an empty response."
- Other errors → "Failed to generate proposal: {sanitized message}"

### 2. Enhanced Forge Endpoint (`server/routes.ts`)

The `/api/forge/:grantId` endpoint orchestrates the proposal generation flow.

#### Endpoint Specification

**Route:** `GET /api/forge/:grantId`

**Query Parameters:**
- `role` (string, required) - Faculty role (e.g., "Assistant Professor")
- `year` (string, required) - Academic year (e.g., "2024")
- `program` (string, required) - Program/department (e.g., "Computer Science")

**Response:** Server-Sent Events (SSE) stream

**SSE Message Format:**
```typescript
// Status update messages
{ step: string, done: false }

// Streaming token messages
{ step: "streaming", done: false, token: string }

// Completion message
{ step: "Complete", done: true, result: { proposal: string } }

// Error message
{ step: string, done: true, error: true }
```

#### Implementation Flow

1. **Extract Parameters:**
   ```typescript
   const { grantId } = req.params;
   const { role, year, program } = req.query;
   ```

2. **Retrieve Grant Record:**
   ```typescript
   const allGrants = await storage.getGrants();
   const grant = allGrants.find(g => g.id === parseInt(grantId));
   if (!grant) {
     res.write(`data: ${JSON.stringify({ 
       step: "Grant not found", 
       done: true, 
       error: true 
     })}\n\n`);
     return res.end();
   }
   ```

3. **Send Status Updates:**
   ```typescript
   const statusSteps = [
     "Sourcing Agent is checking FSU internal policies...",
     "Analyzing applicant history and match criteria...",
     "Drafting proposal summary based on previous successful grants..."
   ];
   
   for (const step of statusSteps) {
     res.write(`data: ${JSON.stringify({ step, done: false })}\n\n`);
     await new Promise(resolve => setTimeout(resolve, 500));
   }
   ```

4. **Stream Proposal Tokens:**
   ```typescript
   const tokens: string[] = [];
   try {
     for await (const token of streamProposal({
       grantName: grant.name,
       role: role as string,
       year: year as string,
       program: program as string,
       matchCriteria: grant.matchCriteria,
       eligibility: grant.eligibility
     })) {
       tokens.push(token);
       res.write(`data: ${JSON.stringify({ 
         step: "streaming", 
         done: false, 
         token 
       })}\n\n`);
     }
   } catch (error) {
     // Error handling (see below)
   }
   ```

5. **Send Completion:**
   ```typescript
   const fullProposal = tokens.join('');
   res.write(`data: ${JSON.stringify({ 
     step: "Complete", 
     done: true, 
     result: { proposal: fullProposal } 
   })}\n\n`);
   res.end();
   ```

#### Error Handling Strategy

**Sanitization Rules:**
- Never expose raw AWS error messages
- Never expose AWS credentials or account IDs
- Never expose internal service names or infrastructure details
- Map AWS errors to user-friendly messages

**Error Mapping:**
```typescript
function sanitizeError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  
  if (message.includes('AccessDenied') || message.includes('access denied')) {
    return 'Service temporarily unavailable. Please try again later.';
  }
  
  if (message.includes('Throttling') || message.includes('high demand')) {
    return 'Service is experiencing high demand. Please try again in a moment.';
  }
  
  if (message.includes('empty response')) {
    return 'Unable to generate proposal at this time. Please try again.';
  }
  
  return 'An error occurred while generating the proposal. Please try again.';
}
```

**Error Response:**
```typescript
catch (error) {
  const sanitizedMessage = sanitizeError(error);
  res.write(`data: ${JSON.stringify({ 
    step: sanitizedMessage, 
    done: true, 
    error: true 
  })}\n\n`);
  res.end();
}
```

### 3. Environment Validator (`server/index.ts`)

Validates required environment variables at server startup.

#### Validation Logic

```typescript
function validateEnvironment(): void {
  const requiredVars = [
    'DATABASE_URL',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_REGION'
  ];
  
  const missing: string[] = [];
  
  for (const varName of requiredVars) {
    if (!process.env[varName]) {
      missing.push(varName);
    }
  }
  
  if (missing.length > 0) {
    console.error('❌ Missing required environment variables:');
    for (const varName of missing) {
      console.error(`   - ${varName}`);
    }
    console.error('\nPlease set these variables in your .env file or environment.');
    process.exit(1);
  }
  
  console.log('✅ Environment validation passed');
}
```

#### Integration Point

```typescript
// In server/index.ts, before app setup
if (process.env.NODE_ENV !== 'production') {
  const dotenv = await import('dotenv');
  dotenv.config();
}

validateEnvironment();

const app = express();
// ... rest of server setup
```

### 4. Storage Layer Extension

The existing storage layer requires a method to retrieve a single grant by ID.

#### New Method

```typescript
// Add to IStorage interface
getGrantById(id: number): Promise<Grant | undefined>;

// Add to DatabaseStorage class
async getGrantById(id: number): Promise<Grant | undefined> {
  const results = await db.select().from(grants).where(eq(grants.id, id));
  return results[0];
}
```

## Data Models

### Existing Models (Unchanged)

From `shared/schema.ts`:

```typescript
export type Grant = {
  id: number;
  name: string;
  targetAudience: string;
  eligibility: string;
  matchCriteria: string;
  internalDeadline: string;
};

export type Faculty = {
  id: number;
  name: string;
  department: string;
  expertise: string;
  imageUrl: string;
  bio: string | null;
};
```

### New Internal Types

```typescript
// In server/bedrock.ts
export interface ProposalParams {
  grantName: string;
  role: string;
  year: string;
  program: string;
  matchCriteria: string;
  eligibility: string;
}

// Bedrock API types (from AWS SDK)
interface BedrockStreamChunk {
  contentBlockDelta?: {
    delta: {
      text: string;
    };
  };
}
```

### SSE Message Types

```typescript
// Status message
type StatusMessage = {
  step: string;
  done: false;
};

// Streaming token message
type StreamingMessage = {
  step: "streaming";
  done: false;
  token: string;
};

// Completion message
type CompletionMessage = {
  step: "Complete";
  done: true;
  result: {
    proposal: string;
  };
};

// Error message
type ErrorMessage = {
  step: string;
  done: true;
  error: true;
};

type SSEMessage = StatusMessage | StreamingMessage | CompletionMessage | ErrorMessage;
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:

**Redundancy Analysis:**
- Properties 2.8 and 2.9 (passing profile parameters and grant details) can be combined into a single property about parameter forwarding
- Properties 4.2, 4.3, and 4.4 (not exposing AWS details, credentials, service names) can be combined into a comprehensive security property
- Properties 6.1, 6.2, and 6.3 (decode chunks, extract tokens, yield strings) are all subsumed by property 6.6 (the round-trip property)
- Properties 3.5 and 3.6 (log error and exit process) can be combined into a single validation failure property

**Consolidated Properties:**
The following properties provide unique validation value without redundancy:

### Property 1: Grant retrieval for valid requests

*For any* valid grantId in a forge request, the endpoint SHALL retrieve the corresponding grant record from storage before invoking the Bedrock client.

**Validates: Requirements 2.3**

### Property 2: Token streaming format preservation

*For any* token yielded by the Bedrock client, the forge endpoint SHALL wrap it in an SSE message with the format `{ step: "streaming", done: false, token: string }`.

**Validates: Requirements 2.5**

### Property 3: Stream completion message

*For any* successfully completed proposal stream, the forge endpoint SHALL send a completion message with format `{ step: "Complete", done: true, result: { proposal: string } }` where the proposal is the concatenation of all streamed tokens.

**Validates: Requirements 2.6**

### Property 4: Parameter forwarding to Bedrock

*For any* forge request with profile parameters (role, year, program) and grant details (matchCriteria, eligibility), all parameters SHALL be passed to the streamProposal function.

**Validates: Requirements 2.8, 2.9**

### Property 5: SSE message format compatibility

*For any* SSE message sent by the forge endpoint, it SHALL conform to one of the existing message formats (status, streaming, completion, or error) to maintain backward compatibility.

**Validates: Requirements 2.10**

### Property 6: Environment validation failure handling

*For any* missing required environment variable (DATABASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION), the validator SHALL log a clear error message identifying the missing variable AND exit the process with a non-zero code.

**Validates: Requirements 3.5, 3.6**

### Property 7: AWS error sanitization

*For any* error originating from AWS Bedrock, the error message sent to the client SHALL NOT contain raw AWS error details, credentials, account IDs, or internal service names.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 8: Stream processing round-trip integrity

*For any* valid proposal request, the tokens yielded by the Bedrock stream processor, when concatenated, SHALL produce a complete and coherent proposal text (validating that streaming preserves content integrity).

**Validates: Requirements 6.6**

### Property 9: System prompt inclusion

*For any* invocation of the Bedrock client, the request payload SHALL include a system prompt field.

**Validates: Requirements 7.1**

### Property 10: Parameter incorporation in user message

*For any* set of proposal parameters (grantName, role, year, program, matchCriteria, eligibility), the user message sent to Bedrock SHALL incorporate all provided parameter values.

**Validates: Requirements 7.4, 7.5**

## Error Handling

### Error Categories

**1. AWS Service Errors**
- AccessDeniedException
- ThrottlingException
- ValidationException
- ServiceUnavailableException

**2. Stream Processing Errors**
- Empty stream body
- Malformed chunk data
- Incomplete content blocks

**3. Application Errors**
- Grant not found
- Missing query parameters
- Invalid parameter values

### Error Handling Strategy

**Principle:** Fail gracefully with user-friendly messages while logging detailed errors server-side.

**Implementation:**

```typescript
// In server/bedrock.ts
export class BedrockError extends Error {
  constructor(
    message: string,
    public readonly userMessage: string,
    public readonly originalError?: unknown
  ) {
    super(message);
    this.name = 'BedrockError';
  }
}

// Error mapping function
function mapAWSError(error: unknown): BedrockError {
  const errorMessage = error instanceof Error ? error.message : String(error);
  
  if (errorMessage.includes('AccessDenied')) {
    return new BedrockError(
      `AWS Access Denied: ${errorMessage}`,
      'Service temporarily unavailable. Please try again later.',
      error
    );
  }
  
  if (errorMessage.includes('Throttling')) {
    return new BedrockError(
      `AWS Throttling: ${errorMessage}`,
      'Service is experiencing high demand. Please try again in a moment.',
      error
    );
  }
  
  return new BedrockError(
    `AWS Error: ${errorMessage}`,
    'An error occurred while generating the proposal. Please try again.',
    error
  );
}
```

**Logging Strategy:**
- Log full error details server-side for debugging
- Include request context (grantId, parameters)
- Never log credentials or sensitive data
- Use structured logging for error tracking

```typescript
// Error logging helper
function logError(context: string, error: unknown, metadata?: Record<string, any>) {
  console.error(`[${context}] Error:`, {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    metadata,
    timestamp: new Date().toISOString()
  });
}
```

### Error Recovery

**Client-Side:**
- Display user-friendly error messages
- Provide retry button for transient errors
- Suggest alternative actions for persistent errors

**Server-Side:**
- Close SSE connections cleanly on errors
- Clean up resources (timers, streams)
- Maintain server stability despite client errors

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples and edge cases
- Integration points between components
- Error conditions with mocked AWS responses
- Environment validation with specific missing variables

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Stream processing integrity across varied token sequences
- Parameter forwarding with random valid inputs

### Property-Based Testing Configuration

**Library Selection:**
- Use `fast-check` for TypeScript/Node.js property-based testing
- Minimum 100 iterations per property test
- Each test references its design document property

**Test Tagging Format:**
```typescript
// Feature: aws-bedrock-backend-integration, Property 1: Grant retrieval for valid requests
test('forge endpoint retrieves grant for any valid grantId', async () => {
  await fc.assert(
    fc.asyncProperty(fc.integer({ min: 1, max: 100 }), async (grantId) => {
      // Test implementation
    }),
    { numRuns: 100 }
  );
});
```

### Unit Test Coverage

**Bedrock Client Module:**
- ✓ Correct model ID is used (example test)
- ✓ System prompt is included in requests (example test)
- ✓ AWS region from environment is used (example test)
- ✓ AccessDeniedException throws descriptive error (edge case)
- ✓ ThrottlingException throws descriptive error (edge case)
- ✓ Empty stream throws descriptive error (edge case)

**Forge Endpoint:**
- ✓ Exactly 3 status messages sent before streaming (example test)
- ✓ Error during streaming sends error message (edge case)
- ✓ AccessDeniedException mapped to "service unavailable" (edge case)
- ✓ Throttling mapped to "high demand" message (edge case)

**Environment Validator:**
- ✓ Missing DATABASE_URL detected (example test)
- ✓ Missing AWS_ACCESS_KEY_ID detected (example test)
- ✓ Missing AWS_SECRET_ACCESS_KEY detected (example test)
- ✓ Missing AWS_REGION detected (example test)
- ✓ Development mode loads dotenv (example test)

**API Contract Preservation:**
- ✓ GET /api/grants returns Grant[] (example test)
- ✓ GET /api/faculty returns Faculty[] (example test)
- ✓ GET /api/forge/:grantId uses SSE (example test)
- ✓ Seeding logic still works (example test)

**System Prompt Content:**
- ✓ Prompt identifies AI as FSU assistant (example test)
- ✓ Prompt instructs to generate proposals (example test)

### Property-Based Test Coverage

**Property 1: Grant retrieval**
```typescript
// Feature: aws-bedrock-backend-integration, Property 1: Grant retrieval for valid requests
fc.asyncProperty(
  fc.integer({ min: 1, max: 1000 }),
  async (grantId) => {
    // Mock storage with grant
    // Make request to /api/forge/:grantId
    // Verify storage.getGrants() was called
  }
);
```

**Property 2: Token streaming format**
```typescript
// Feature: aws-bedrock-backend-integration, Property 2: Token streaming format preservation
fc.asyncProperty(
  fc.array(fc.string({ minLength: 1, maxLength: 100 })),
  async (tokens) => {
    // Mock Bedrock to yield these tokens
    // Verify each SSE message has correct format
  }
);
```

**Property 3: Stream completion**
```typescript
// Feature: aws-bedrock-backend-integration, Property 3: Stream completion message
fc.asyncProperty(
  fc.array(fc.string()),
  async (tokens) => {
    // Mock Bedrock to yield tokens
    // Verify completion message contains concatenated tokens
  }
);
```

**Property 4: Parameter forwarding**
```typescript
// Feature: aws-bedrock-backend-integration, Property 4: Parameter forwarding to Bedrock
fc.asyncProperty(
  fc.record({
    role: fc.string(),
    year: fc.string(),
    program: fc.string(),
    grantName: fc.string(),
    matchCriteria: fc.string(),
    eligibility: fc.string()
  }),
  async (params) => {
    // Make request with these params
    // Verify streamProposal called with all params
  }
);
```

**Property 5: SSE format compatibility**
```typescript
// Feature: aws-bedrock-backend-integration, Property 5: SSE message format compatibility
fc.asyncProperty(
  fc.oneof(
    fc.constant('status'),
    fc.constant('streaming'),
    fc.constant('completion'),
    fc.constant('error')
  ),
  async (messageType) => {
    // Generate scenario for each message type
    // Verify message conforms to expected format
  }
);
```

**Property 6: Environment validation**
```typescript
// Feature: aws-bedrock-backend-integration, Property 6: Environment validation failure handling
fc.property(
  fc.constantFrom('DATABASE_URL', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION'),
  (missingVar) => {
    // Remove this env var
    // Call validator
    // Verify error logged and process.exit called
  }
);
```

**Property 7: AWS error sanitization**
```typescript
// Feature: aws-bedrock-backend-integration, Property 7: AWS error sanitization
fc.asyncProperty(
  fc.record({
    errorType: fc.constantFrom('AccessDenied', 'Throttling', 'Validation'),
    awsAccountId: fc.string(),
    awsRegion: fc.string(),
    credentials: fc.string()
  }),
  async (errorData) => {
    // Mock AWS error with sensitive data
    // Verify client message doesn't contain sensitive data
  }
);
```

**Property 8: Stream round-trip integrity**
```typescript
// Feature: aws-bedrock-backend-integration, Property 8: Stream processing round-trip integrity
fc.asyncProperty(
  fc.array(fc.string({ minLength: 1 }), { minLength: 1 }),
  async (tokens) => {
    // Mock Bedrock stream with these tokens
    // Process through streamProposal
    // Verify concatenated output equals joined tokens
  }
);
```

**Property 9: System prompt inclusion**
```typescript
// Feature: aws-bedrock-backend-integration, Property 9: System prompt inclusion
fc.asyncProperty(
  fc.record({
    grantName: fc.string(),
    role: fc.string(),
    year: fc.string(),
    program: fc.string(),
    matchCriteria: fc.string(),
    eligibility: fc.string()
  }),
  async (params) => {
    // Call streamProposal with params
    // Verify AWS SDK called with system prompt field
  }
);
```

**Property 10: Parameter incorporation**
```typescript
// Feature: aws-bedrock-backend-integration, Property 10: Parameter incorporation in user message
fc.asyncProperty(
  fc.record({
    grantName: fc.string({ minLength: 1 }),
    role: fc.string({ minLength: 1 }),
    year: fc.string({ minLength: 1 }),
    program: fc.string({ minLength: 1 }),
    matchCriteria: fc.string({ minLength: 1 }),
    eligibility: fc.string({ minLength: 1 })
  }),
  async (params) => {
    // Call streamProposal with params
    // Verify user message contains all parameter values
  }
);
```

### Test Environment Setup

**Mocking Strategy:**
- Mock AWS SDK BedrockRuntimeClient for unit tests
- Use test doubles for storage layer
- Mock environment variables for validation tests
- Use in-memory SSE capture for endpoint tests

**Test Data:**
- Generate realistic grant records
- Create varied faculty profiles
- Use diverse token sequences for streaming tests
- Include edge cases (empty strings, special characters, very long inputs)

### Integration Testing

**End-to-End Flow:**
1. Start server with test environment variables
2. Seed test database with grants
3. Make SSE request to /api/forge/:grantId
4. Verify complete flow from request to completion
5. Validate SSE message sequence
6. Confirm proposal content quality

**Performance Testing:**
- Measure streaming latency
- Test concurrent requests
- Verify memory usage during long streams
- Validate connection cleanup

## Implementation Notes

### Dependency Installation

Add to `package.json`:
```json
{
  "dependencies": {
    "@aws-sdk/client-bedrock-runtime": "^3.600.0",
    "dotenv": "^16.4.5"
  },
  "devDependencies": {
    "fast-check": "^3.15.0",
    "@types/node": "^20.11.0"
  }
}
```

### File Changes Summary

**New Files:**
- `server/bedrock.ts` - Bedrock client module with streaming logic

**Modified Files:**
- `server/index.ts` - Add environment validation
- `server/routes.ts` - Update /api/forge/:grantId endpoint
- `server/storage.ts` - Add getGrantById method (optional optimization)
- `package.json` - Add AWS SDK and dotenv dependencies

**Unchanged Files:**
- `shared/schema.ts` - No schema changes required
- `client/*` - No frontend changes required
- All other server files remain unchanged

### Environment Variables

Required variables (add to `.env` for development):
```
DATABASE_URL=postgresql://user:password@localhost:5432/fundingforge
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
```

### Deployment Considerations

**AWS Permissions Required:**
- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`

**IAM Policy Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-haiku-20240307-v1:0"
    }
  ]
}
```

**Cost Considerations:**
- Claude 3 Haiku pricing: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- Typical proposal: ~500 input tokens, ~2000 output tokens
- Estimated cost per proposal: ~$0.0025

**Monitoring:**
- Track Bedrock API latency
- Monitor token usage and costs
- Alert on high error rates
- Log throttling events for capacity planning

### Security Best Practices

1. **Credential Management:**
   - Never commit credentials to version control
   - Use environment variables or AWS IAM roles
   - Rotate credentials regularly
   - Use least-privilege IAM policies

2. **Error Handling:**
   - Sanitize all error messages before sending to clients
   - Log detailed errors server-side only
   - Never expose AWS account IDs or internal infrastructure details

3. **Input Validation:**
   - Validate grantId is a positive integer
   - Sanitize query parameters before passing to Bedrock
   - Limit proposal length to prevent abuse
   - Rate limit requests per user/IP

4. **Output Validation:**
   - Verify proposal content is appropriate
   - Filter any potentially sensitive information
   - Validate token format before sending to client

### Performance Optimization

**Streaming Benefits:**
- Reduces time-to-first-token for better UX
- Allows client to display partial results
- Prevents timeout on long-running requests

**Caching Strategy (Future Enhancement):**
- Cache proposals for identical grant/profile combinations
- Use Redis for distributed caching
- Set TTL based on grant deadline proximity

**Connection Management:**
- Implement request timeout (e.g., 60 seconds)
- Clean up SSE connections on client disconnect
- Use connection pooling for database queries

### Backward Compatibility Verification

**Checklist:**
- ✓ Existing API endpoints unchanged
- ✓ SSE message format preserved
- ✓ Database schema unchanged
- ✓ Frontend code requires no modifications
- ✓ Seeding logic preserved
- ✓ Grant and Faculty types unchanged

**Migration Path:**
- Deploy backend changes
- Verify environment variables in production
- Test /api/forge endpoint with real requests
- Monitor for errors and performance issues
- No frontend deployment required

## Conclusion

This design integrates AWS Bedrock into the FundingForge backend while maintaining complete backward compatibility. The modular architecture isolates AWS-specific logic in the Bedrock client module, making it easy to test, maintain, and potentially swap providers in the future.

Key design decisions:
- **Encapsulation:** AWS SDK interactions isolated in dedicated module
- **Security:** Multi-layer error sanitization prevents information leakage
- **Reliability:** Comprehensive error handling and validation
- **Testability:** Clear interfaces enable thorough unit and property-based testing
- **Compatibility:** Zero frontend changes required

The implementation follows Express.js best practices, maintains the existing SSE streaming pattern, and adds production-ready AI capabilities with minimal code changes.
