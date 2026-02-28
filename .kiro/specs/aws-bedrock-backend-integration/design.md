# Design Document: AWS Bedrock Backend Integration

## Overview

This design upgrades the FundingForge backend to integrate a real multi-agent AI pipeline powered by AWS Strands Agents SDK (Python). The system replaces hardcoded mock steps with a FastAPI microservice that orchestrates five specialized agents using AWS Bedrock models. The Express backend connects to the agent service through AWS AgentCore and proxies streaming results via Server-Sent Events (SSE) while preserving all existing API contracts to ensure zero frontend changes.

The architecture introduces:
1. **Python Agent Service** - FastAPI microservice running five specialized agents built with Strands Agents SDK
2. **Five Specialized Agents** - SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent, and OrchestratorAgent
3. **AWS AgentCore Integration** - Manages agent lifecycle and communication between Express backend and agent service
4. **Express SSE Proxy** - Transforms agent JSON_Line outputs to SSE format for frontend consumption
5. **Local Development Support** - Full stack runs locally with localhost configuration

The design prioritizes modularity, testability, and graceful degradation. All agents are built using the Strands Agents SDK with BedrockModel wrappers, and the system falls back to mock steps if the agent service is unreachable.

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    Client[Frontend Client]
    Express[Express Backend]
    AgentCore[AWS AgentCore]
    AgentService[Python Agent Service<br/>FastAPI]
    Orchestrator[OrchestratorAgent]
    Sourcing[SourcingAgent<br/>Haiku]
    Matching[MatchmakingAgent<br/>Haiku]
    Collab[CollaboratorAgent<br/>Haiku]
    Drafting[DraftingAgent<br/>Sonnet]
    DB[(PostgreSQL)]
    Bedrock[AWS Bedrock]

    Client -->|SSE Request| Express
    Express -->|Query Grants & Faculty| DB
    Express -->|Invoke via AgentCore| AgentCore
    AgentCore -->|Manage Lifecycle| AgentService
    AgentService -->|Coordinate| Orchestrator
    Orchestrator -->|Execute Sequence| Sourcing
    Orchestrator -->|Execute Sequence| Matching
    Orchestrator -->|Execute Sequence| Collab
    Orchestrator -->|Execute Sequence| Drafting
    Sourcing -->|Invoke Model| Bedrock
    Matching -->|Invoke Model| Bedrock
    Collab -->|Invoke Model| Bedrock
    Drafting -->|Invoke Model| Bedrock
    AgentService -->|Stream JSON_Line| AgentCore
    AgentCore -->|Stream JSON_Line| Express
    Express -->|Transform to SSE| Client
```

### Agent Pipeline Flow

```mermaid
sequenceDiagram
    participant Client
    participant Express
    participant AgentCore
    participant Orchestrator
    participant Sourcing
    participant Matching
    participant Collab
    participant Drafting
    participant Bedrock

    Client->>Express: GET /api/forge/:grantId?role=X&year=Y&program=Z
    Express->>Express: Fetch grant and faculty from DB
    Express->>AgentCore: Invoke with payload
    AgentCore->>Orchestrator: Start pipeline
    
    Orchestrator->>Sourcing: Extract user data
    Sourcing->>Bedrock: Invoke Haiku
    Bedrock-->>Sourcing: Stream response
    Sourcing-->>Orchestrator: Return structured data
    Orchestrator-->>Express: JSON_Line: "SourcingAgent: Extracted CV data"
    Express-->>Client: SSE: "SourcingAgent: Extracted CV data"
    
    Orchestrator->>Matching: Analyze match & compliance
    Matching->>Bedrock: Invoke Haiku
    Bedrock-->>Matching: Stream response
    Matching-->>Orchestrator: Return score & checklist
    Orchestrator-->>Express: JSON_Line: "MatchmakingAgent: Match score 85%"
    Express-->>Client: SSE: "MatchmakingAgent: Match score 85%"
    
    Orchestrator->>Collab: Find collaborators
    Collab->>Bedrock: Invoke Haiku
    Bedrock-->>Collab: Stream response
    Collab-->>Orchestrator: Return top 3 faculty
    Orchestrator-->>Express: JSON_Line: "CollaboratorAgent: Found 3 matches"
    Express-->>Client: SSE: "CollaboratorAgent: Found 3 matches"
    
    Orchestrator->>Drafting: Generate proposal
    Drafting->>Bedrock: Invoke Sonnet
    Bedrock-->>Drafting: Stream response
    Drafting-->>Orchestrator: Return proposal draft
    Orchestrator-->>Express: JSON_Line: "DraftingAgent: Generated 450-word draft"
    Express-->>Client: SSE: "DraftingAgent: Generated 450-word draft"
    
    Orchestrator-->>Express: JSON_Line: done=true with Result_Payload
    Express-->>Client: SSE: Complete with result
```

### Local Development Architecture

```mermaid
graph LR
    Dev[Developer Machine]
    subgraph "Localhost Services"
        Express[Express:5000]
        AgentCore[AgentCore:8000]
        Agent[Agent Service:8001]
        DB[(PostgreSQL:5432)]
    end
    Bedrock[AWS Bedrock<br/>us-east-1]
    
    Dev -->|Browser| Express
    Express -->|localhost:8000| AgentCore
    AgentCore -->|localhost:8001| Agent
    Express -->|Query| DB
    Agent -->|AWS SDK| Bedrock
```

## Components and Interfaces

### 1. Python Agent Service (FastAPI)

The agent service is a Python FastAPI microservice that orchestrates the five-agent pipeline.

#### Service Specification

**Framework:** FastAPI  
**Port:** 8001  
**Location:** `/agent-service/`  
**Runtime:** uvicorn

#### API Endpoint

**Route:** `POST /invoke`

**Request Body:**
```typescript
{
  grantId: number;
  grantName: string;
  matchCriteria: string;
  eligibility: string;
  userProfile: {
    role: string;
    year: string;
    program: string;
  };
  facultyList: Array<{
    name: string;
    department: string;
    expertise: string;
    imageUrl: string;
    bio: string | null;
  }>;
}
```

**Response:** Streaming JSON_Line format (newline-delimited JSON)

**JSON_Line Format:**
```typescript
{
  agent: string;        // "sourcing" | "matchmaking" | "collaborator" | "drafting" | "orchestrator"
  step: string;         // Human-readable progress message
  output: any;          // Agent-specific output data
  done: boolean;        // true only for final message
}
```

**Final JSON_Line (done=true):**
```typescript
{
  agent: "orchestrator";
  step: "Complete";
  output: {
    proposalDraft: string;
    collaborators: Array<{
      name: string;
      department: string;
      expertise: string;
      relevanceScore: number;
    }>;
    matchScore: number;           // 0-100
    matchJustification: string;
    complianceChecklist: Array<{
      task: string;
      category: "RAMP" | "COI" | "IRB" | "Policy";
      status: "green" | "yellow" | "red";
    }>;
  };
  done: true;
}
```

#### Implementation Structure

```python
# agent-service/main.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from strands import Agent
from strands.models import BedrockModel
import json

app = FastAPI()

# Model instantiation
drafting_model = BedrockModel(model_id="anthropic.claude-sonnet-4-6")
fast_model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# Agent instantiation (details in agent sections below)
sourcing_agent = Agent(model=fast_model, system_prompt="...")
matchmaking_agent = Agent(model=fast_model, system_prompt="...")
collaborator_agent = Agent(model=fast_model, system_prompt="...")
drafting_agent = Agent(model=drafting_model, system_prompt="...")
orchestrator_agent = Agent(...)  # Coordinates all agents

@app.post("/invoke")
async def invoke_pipeline(request: InvokeRequest):
    async def generate():
        async for line in orchestrator_agent.run(request):
            yield json.dumps(line) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")
```

### 2. SourcingAgent

Extracts and structures relevant data from user CV and profile.

#### Agent Configuration

**Model:** BedrockModel with `anthropic.claude-haiku-4-5-20251001-v1:0`  
**Purpose:** Source and structure user experience, publications, and expertise

#### System Prompt

```
You are the SourcingAgent for FundingForge. Your role is to extract and structure relevant information from a user's CV and profile to support grant proposal generation.

Given a user profile with role, year, and program, extract:
1. Relevant experience and accomplishments
2. Publications and research output
3. Expertise areas and technical skills
4. Academic background and credentials

Return structured data that downstream agents can use to assess grant fit and generate proposals.

Output format: JSON with fields experience, publications, expertise, credentials.
```

#### Input/Output

**Input:**
- userProfile: { role, year, program }
- (Future: CV text, profile data)

**Output:**
```typescript
{
  experience: string[];
  publications: string[];
  expertise: string[];
  credentials: string[];
}
```

#### Streaming Behavior

Emits JSON_Line messages:
```json
{"agent": "sourcing", "step": "Extracting CV data...", "output": null, "done": false}
{"agent": "sourcing", "step": "Identified 5 publications", "output": null, "done": false}
{"agent": "sourcing", "step": "Complete", "output": {...}, "done": true}
```

### 3. MatchmakingAgent

Analyzes user profile against grant criteria AND checks policy/compliance requirements.

#### Agent Configuration

**Model:** BedrockModel with `anthropic.claude-haiku-4-5-20251001-v1:0`  
**Purpose:** Dual responsibility - match scoring AND compliance checking

#### System Prompt

```
You are the MatchmakingAgent for FundingForge. You have two critical responsibilities:

1. MATCH ANALYSIS: Analyze how well the user's profile matches the grant's criteria
   - Compare user expertise against grant requirements
   - Assess eligibility fit
   - Generate a match score (0-100) and justification

2. COMPLIANCE CHECKING: Verify policy and regulatory requirements
   - FSU internal policies
   - RAMP (Research Administration and Management Portal) requirements
   - COI (Conflict of Interest) triggers
   - IRB (Institutional Review Board) checkpoints

For each compliance item, determine:
- task: What needs to be checked/completed
- category: RAMP, COI, IRB, or Policy
- status: green (compliant), yellow (needs attention), red (blocker)

Output format: JSON with matchScore, matchJustification, complianceChecklist.
```

#### Input/Output

**Input:**
- userProfile: { role, year, program }
- sourcedData: Output from SourcingAgent
- matchCriteria: string
- eligibility: string

**Output:**
```typescript
{
  matchScore: number;              // 0-100
  matchJustification: string;
  complianceChecklist: Array<{
    task: string;
    category: "RAMP" | "COI" | "IRB" | "Policy";
    status: "green" | "yellow" | "red";
  }>;
}
```

#### Streaming Behavior

Emits JSON_Line messages:
```json
{"agent": "matchmaking", "step": "Analyzing match criteria...", "output": null, "done": false}
{"agent": "matchmaking", "step": "Checking FSU policies...", "output": null, "done": false}
{"agent": "matchmaking", "step": "Checking RAMP requirements...", "output": null, "done": false}
{"agent": "matchmaking", "step": "Identifying COI triggers...", "output": null, "done": false}
{"agent": "matchmaking", "step": "Checking IRB requirements...", "output": null, "done": false}
{"agent": "matchmaking", "step": "Match score: 85%", "output": null, "done": false}
{"agent": "matchmaking", "step": "Complete", "output": {...}, "done": true}
```

### 4. CollaboratorAgent

Finds and ranks relevant faculty collaborators based on expertise.

#### Agent Configuration

**Model:** BedrockModel with `anthropic.claude-haiku-4-5-20251001-v1:0`  
**Purpose:** Match faculty based on program and expertise keywords

#### System Prompt

```
You are the CollaboratorAgent for FundingForge. Your role is to identify the most relevant faculty collaborators for a grant proposal.

Given:
- A list of faculty members with their departments, expertise, and bios
- Grant requirements and match criteria
- User's program and research area

Identify the top 3 faculty members who would strengthen the proposal. For each:
- Assess relevance based on expertise alignment
- Consider departmental fit
- Generate a relevance score (0-100)

Output format: JSON array with name, department, expertise, relevanceScore for top 3 matches.
```

#### Input/Output

**Input:**
- facultyList: Array of faculty records
- matchCriteria: string
- userProfile: { role, year, program }

**Output:**
```typescript
{
  collaborators: Array<{
    name: string;
    department: string;
    expertise: string;
    relevanceScore: number;  // 0-100
  }>;  // Top 3 only
}
```

#### Streaming Behavior

Emits JSON_Line messages:
```json
{"agent": "collaborator", "step": "Analyzing faculty expertise...", "output": null, "done": false}
{"agent": "collaborator", "step": "Matching against grant criteria...", "output": null, "done": false}
{"agent": "collaborator", "step": "Found 3 relevant collaborators", "output": null, "done": false}
{"agent": "collaborator", "step": "Complete", "output": {...}, "done": true}
```

### 5. DraftingAgent

Generates high-quality proposal narrative scaffold using the most capable model.

#### Agent Configuration

**Model:** BedrockModel with `anthropic.claude-sonnet-4-6` (HIGHEST QUALITY)  
**Purpose:** Generate compelling proposal narrative

#### System Prompt

```
You are the DraftingAgent for FundingForge. You are powered by Claude Sonnet, the highest-quality model in the pipeline, because your output directly represents the proposal quality.

Your role is to generate a compelling grant proposal narrative scaffold based on:
- Grant requirements and criteria
- User's profile and expertise
- Match justification
- Recommended collaborators

Generate a professional proposal narrative between 300-500 words that includes:
- Clear section headers (Introduction, Objectives, Methodology, Impact)
- Persuasive academic language
- Integration of user's strengths
- Alignment with grant criteria

Output format: Plain text with section headers.
```

#### Input/Output

**Input:**
- grantName: string
- matchCriteria: string
- eligibility: string
- matchJustification: string
- sourcedData: Output from SourcingAgent
- collaborators: Output from CollaboratorAgent

**Output:**
```typescript
{
  proposalDraft: string;  // 300-500 words with section headers
}
```

#### Streaming Behavior

Emits JSON_Line messages:
```json
{"agent": "drafting", "step": "Generating proposal structure...", "output": null, "done": false}
{"agent": "drafting", "step": "Writing introduction...", "output": null, "done": false}
{"agent": "drafting", "step": "Drafting methodology section...", "output": null, "done": false}
{"agent": "drafting", "step": "Generated 450-word draft", "output": null, "done": false}
{"agent": "drafting", "step": "Complete", "output": {...}, "done": true}
```

### 6. OrchestratorAgent

Coordinates execution of all four specialized agents in sequence.

#### Agent Configuration

**Purpose:** Manage data flow and execution order across all agents

#### Orchestration Logic

```python
async def orchestrate_pipeline(request: InvokeRequest):
    """
    Executes agents in sequence: Sourcing → Matchmaking → Collaborator → Drafting
    Manages data flow between agents and emits progress updates
    """
    
    # Step 1: SourcingAgent
    yield {"agent": "orchestrator", "step": "Starting SourcingAgent...", "output": None, "done": False}
    sourced_data = await sourcing_agent.run(request.userProfile)
    yield {"agent": "sourcing", "step": "Extracted user data", "output": None, "done": False}
    
    # Step 2: MatchmakingAgent
    yield {"agent": "orchestrator", "step": "Starting MatchmakingAgent...", "output": None, "done": False}
    match_result = await matchmaking_agent.run({
        "userProfile": request.userProfile,
        "sourcedData": sourced_data,
        "matchCriteria": request.matchCriteria,
        "eligibility": request.eligibility
    })
    yield {"agent": "matchmaking", "step": f"Match score: {match_result.matchScore}%", "output": None, "done": False}
    
    # Step 3: CollaboratorAgent
    yield {"agent": "orchestrator", "step": "Starting CollaboratorAgent...", "output": None, "done": False}
    collab_result = await collaborator_agent.run({
        "facultyList": request.facultyList,
        "matchCriteria": request.matchCriteria,
        "userProfile": request.userProfile
    })
    yield {"agent": "collaborator", "step": f"Found {len(collab_result.collaborators)} collaborators", "output": None, "done": False}
    
    # Step 4: DraftingAgent
    yield {"agent": "orchestrator", "step": "Starting DraftingAgent...", "output": None, "done": False}
    draft_result = await drafting_agent.run({
        "grantName": request.grantName,
        "matchCriteria": request.matchCriteria,
        "eligibility": request.eligibility,
        "matchJustification": match_result.matchJustification,
        "sourcedData": sourced_data,
        "collaborators": collab_result.collaborators
    })
    yield {"agent": "drafting", "step": "Generated proposal draft", "output": None, "done": False}
    
    # Final result
    yield {
        "agent": "orchestrator",
        "step": "Complete",
        "output": {
            "proposalDraft": draft_result.proposalDraft,
            "collaborators": collab_result.collaborators,
            "matchScore": match_result.matchScore,
            "matchJustification": match_result.matchJustification,
            "complianceChecklist": match_result.complianceChecklist
        },
        "done": True
    }
```

#### Data Flow Management

The OrchestratorAgent ensures:
1. Sequential execution (no parallel execution to maintain data dependencies)
2. Output from each agent is passed to subsequent agents as needed
3. Progress updates are emitted after each agent completes
4. Final result aggregates outputs from all agents
5. No markdown fencing in JSON responses

### 7. AWS AgentCore Integration

AWS AgentCore manages agent lifecycle and communication between Express backend and agent service.

#### AgentCore Responsibilities

1. **Agent Lifecycle Management**
   - Start/stop agent service instances
   - Health monitoring
   - Resource allocation

2. **Communication Layer**
   - Route requests from Express to agent service
   - Stream responses back to Express
   - Handle connection failures

3. **Local Development Support**
   - Run locally on port 8000
   - Connect to localhost:8001 (agent service)
   - Use local AWS credentials

#### Express Backend Integration

```typescript
// server/agentcore-client.ts
import { AgentCoreClient } from '@aws-sdk/client-agentcore';

const agentCoreClient = new AgentCoreClient({
  region: process.env.AWS_REGION,
  endpoint: process.env.AGENTCORE_ENDPOINT || 'http://localhost:8000'
});

export async function* invokeAgentPipeline(payload: InvokePayload): AsyncGenerator<JSONLine> {
  const response = await agentCoreClient.invokeAgent({
    agentId: 'fundingforge-pipeline',
    payload: JSON.stringify(payload)
  });
  
  // Stream JSON_Line responses
  for await (const chunk of response.stream) {
    const line = JSON.parse(chunk.toString());
    yield line;
  }
}
```

#### Configuration

**Environment Variables:**
- `AGENTCORE_ENDPOINT`: URL for AgentCore (default: http://localhost:8000)
- `AGENT_SERVICE_URL`: URL for agent service (used by AgentCore, default: http://localhost:8001)

### 8. Express Backend SSE Proxy

The Express backend transforms agent JSON_Line outputs to SSE format for frontend consumption.

#### Enhanced Forge Endpoint

**Route:** `GET /api/forge/:grantId`

**Query Parameters:**
- `role` (string, required)
- `year` (string, required)
- `program` (string, required)

**Response:** Server-Sent Events (SSE) stream

#### Implementation

```typescript
// server/routes.ts
app.get('/api/forge/:grantId', async (req, res) => {
  const { grantId } = req.params;
  const { role, year, program } = req.query;
  
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  try {
    // Fetch grant and faculty from database
    const grant = await storage.getGrantById(parseInt(grantId));
    if (!grant) {
      res.write(`data: ${JSON.stringify({ 
        step: "Grant not found", 
        done: true, 
        error: true 
      })}\n\n`);
      return res.end();
    }
    
    const facultyList = await storage.getFaculty();
    
    // Build payload for agent service
    const payload = {
      grantId: grant.id,
      grantName: grant.name,
      matchCriteria: grant.matchCriteria,
      eligibility: grant.eligibility,
      userProfile: {
        role: role as string,
        year: year as string,
        program: program as string
      },
      facultyList: facultyList.map(f => ({
        name: f.name,
        department: f.department,
        expertise: f.expertise,
        imageUrl: f.imageUrl,
        bio: f.bio
      }))
    };
    
    // Invoke through AgentCore with fallback
    try {
      for await (const jsonLine of invokeAgentPipeline(payload)) {
        if (jsonLine.done) {
          // Final message with result
          res.write(`data: ${JSON.stringify({
            step: "Complete",
            done: true,
            result: jsonLine.output
          })}\n\n`);
        } else {
          // Progress message
          res.write(`data: ${JSON.stringify({
            step: `${jsonLine.agent}: ${jsonLine.step}`,
            done: false
          })}\n\n`);
        }
      }
    } catch (agentError) {
      // Fallback to mock steps
      console.warn('Agent service unreachable, falling back to mock steps:', agentError);
      await sendMockSteps(res, grant, role as string, year as string, program as string);
    }
    
    res.end();
  } catch (error) {
    res.write(`data: ${JSON.stringify({
      step: "An error occurred",
      done: true,
      error: true
    })}\n\n`);
    res.end();
  }
});
```

#### Graceful Degradation (Mock Fallback)

```typescript
async function sendMockSteps(res: Response, grant: Grant, role: string, year: string, program: string) {
  const mockSteps = [
    "SourcingAgent: Extracting CV data...",
    "MatchmakingAgent: Analyzing match criteria...",
    "MatchmakingAgent: Checking FSU policies...",
    "CollaboratorAgent: Finding relevant faculty...",
    "DraftingAgent: Generating proposal draft..."
  ];
  
  for (const step of mockSteps) {
    res.write(`data: ${JSON.stringify({ step, done: false })}\n\n`);
    await new Promise(resolve => setTimeout(resolve, 800));
  }
  
  // Mock result
  const mockResult = {
    proposalDraft: `Mock proposal for ${grant.name}...`,
    collaborators: [
      { name: "Dr. Smith", department: "Computer Science", expertise: "AI", relevanceScore: 85 }
    ],
    matchScore: 75,
    matchJustification: "Mock justification",
    complianceChecklist: [
      { task: "Submit RAMP form", category: "RAMP", status: "yellow" }
    ]
  };
  
  res.write(`data: ${JSON.stringify({
    step: "Complete",
    done: true,
    result: mockResult
  })}\n\n`);
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

### New Schema Extensions

#### Forge Stream Chunk (Updated)

```typescript
// shared/routes.ts
export const forgeStreamChunkSchema = z.object({
  step: z.string(),
  done: z.boolean(),
  error: z.boolean().optional(),
  result: z.object({
    proposalDraft: z.string(),
    collaborators: z.array(z.object({
      name: z.string(),
      department: z.string(),
      expertise: z.string(),
      relevanceScore: z.number()
    })),
    matchScore: z.number().min(0).max(100),
    matchJustification: z.string(),
    complianceChecklist: z.array(z.object({
      task: z.string(),
      category: z.enum(["RAMP", "COI", "IRB", "Policy"]),
      status: z.enum(["green", "yellow", "red"])
    }))
  }).optional()
});

export type ForgeStreamChunk = z.infer<typeof forgeStreamChunkSchema>;
```

#### Agent Service Types

```python
# agent-service/models.py
from pydantic import BaseModel
from typing import List, Optional, Literal

class UserProfile(BaseModel):
    role: str
    year: str
    program: str

class FacultyMember(BaseModel):
    name: str
    department: str
    expertise: str
    imageUrl: str
    bio: Optional[str]

class InvokeRequest(BaseModel):
    grantId: int
    grantName: str
    matchCriteria: str
    eligibility: str
    userProfile: UserProfile
    facultyList: List[FacultyMember]

class Collaborator(BaseModel):
    name: str
    department: str
    expertise: str
    relevanceScore: float

class ComplianceItem(BaseModel):
    task: str
    category: Literal["RAMP", "COI", "IRB", "Policy"]
    status: Literal["green", "yellow", "red"]

class ResultPayload(BaseModel):
    proposalDraft: str
    collaborators: List[Collaborator]
    matchScore: float
    matchJustification: str
    complianceChecklist: List[ComplianceItem]

class JSONLine(BaseModel):
    agent: str
    step: str
    output: Optional[dict]
    done: bool
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:

**Redundancy Analysis:**
- Properties 2.6, 3.10, 4.5, 5.6 (all agents streaming JSON_Line with same fields) can be combined into one comprehensive property about JSON_Line format
- Properties 2.7, 3.11, 4.6, 5.7 (all agents setting done=true on completion) can be combined into one property about completion signaling
- Properties 3.3, 3.4, 3.5, 3.6 (checking FSU policies, RAMP, COI, IRB) are all part of MatchmakingAgent's compliance checking and can be validated by checking the compliance checklist output
- Properties 8.1 and 8.2 (fetching grant and faculty) can be combined into one property about database queries
- Properties 8.6 and 8.7 (SSE transformation for progress and completion) can be combined into one comprehensive property about SSE format
- Properties 15.2, 15.4, 15.5 (JSON validation, string escaping, numeric validation) can be combined into one property about JSON validity
- Properties 17.3 and 17.4 (passing grant and faculty fields) are covered by 8.3 (building complete payload)

**Consolidated Properties:**
The following properties provide unique validation value without redundancy:

### Property 1: Agent service endpoint existence

*For any* POST request to /invoke endpoint, the agent service SHALL respond (not 404).

**Validates: Requirements 1.2**

### Property 2: Request payload validation

*For any* request with all required fields (grantId, grantName, matchCriteria, eligibility, userProfile, facultyList), the agent service SHALL accept it; for any request missing required fields, the agent service SHALL reject it.

**Validates: Requirements 1.3**

### Property 3: AgentCore URL configuration

*For any* valid URL set in AGENT_SERVICE_URL environment variable, the Express backend SHALL use that URL for agent invocation.

**Validates: Requirements 1.7**

### Property 4: Graceful degradation on service failure

*For any* unreachable agent service, the Express backend SHALL fall back to mock steps and log a console.warn message.

**Validates: Requirements 1.8, 12.1, 12.2**


### Property 5: SourcingAgent model configuration

*For any* SourcingAgent instantiation, it SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0".

**Validates: Requirements 2.1**

### Property 6: SourcingAgent data extraction

*For any* user profile input, the SourcingAgent SHALL extract experience, publications, and expertise areas and return structured data.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5**

### Property 7: JSON_Line streaming format

*For any* agent streaming output (SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent), each JSON_Line SHALL contain fields: agent, step, output, done.

**Validates: Requirements 2.6, 3.10, 4.5, 5.6**

### Property 8: Agent completion signaling

*For any* agent that completes processing, the final JSON_Line SHALL have done=true.

**Validates: Requirements 2.7, 3.11, 4.6, 5.7**

### Property 9: MatchmakingAgent model configuration

*For any* MatchmakingAgent instantiation, it SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0".

**Validates: Requirements 3.1**

### Property 10: MatchmakingAgent dual responsibility

*For any* MatchmakingAgent invocation, it SHALL analyze user profile against grant criteria AND check compliance (FSU policies, RAMP, COI, IRB).

**Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**

### Property 11: Match score range validation

*For any* MatchmakingAgent output, the match score SHALL be a number between 0 and 100 (inclusive).

**Validates: Requirements 3.7**

### Property 12: Match justification presence

*For any* MatchmakingAgent output, there SHALL be a non-empty justification string explaining the match score.

**Validates: Requirements 3.8**

### Property 13: Compliance checklist structure

*For any* MatchmakingAgent output, the compliance checklist SHALL contain items with task (string), category (RAMP|COI|IRB|Policy), and status (green|yellow|red).

**Validates: Requirements 3.9**


### Property 14: DraftingAgent model configuration

*For any* DraftingAgent instantiation, it SHALL use BedrockModel with model_id "anthropic.claude-sonnet-4-6".

**Validates: Requirements 4.1**

### Property 15: DraftingAgent input incorporation

*For any* DraftingAgent invocation, it SHALL receive and use grant context and match justification as inputs.

**Validates: Requirements 4.2**

### Property 16: Proposal word count constraint

*For any* DraftingAgent output, the proposal narrative SHALL contain between 300 and 500 words (inclusive).

**Validates: Requirements 4.3**

### Property 17: Proposal section headers

*For any* DraftingAgent output, the proposal narrative SHALL include labeled section headers.

**Validates: Requirements 4.4**

### Property 18: CollaboratorAgent model configuration

*For any* CollaboratorAgent instantiation, it SHALL use BedrockModel with model_id "anthropic.claude-haiku-4-5-20251001-v1:0".

**Validates: Requirements 5.1**

### Property 19: CollaboratorAgent faculty input

*For any* CollaboratorAgent invocation, it SHALL receive the full faculty list from the database.

**Validates: Requirements 5.2**

### Property 20: CollaboratorAgent matching logic

*For any* CollaboratorAgent invocation with faculty list and criteria, it SHALL match faculty based on program and expertise keywords.

**Validates: Requirements 5.3**

### Property 21: Top collaborators limit

*For any* CollaboratorAgent output, it SHALL return at most 3 faculty members.

**Validates: Requirements 5.4**

### Property 22: Collaborator relevance scores

*For any* faculty member in CollaboratorAgent output, there SHALL be a relevance score included.

**Validates: Requirements 5.5**


### Property 23: OrchestratorAgent execution completeness

*For any* pipeline execution, the OrchestratorAgent SHALL invoke all four specialized agents (SourcingAgent, MatchmakingAgent, CollaboratorAgent, DraftingAgent).

**Validates: Requirements 6.1**

### Property 24: Agent execution order

*For any* pipeline execution, the OrchestratorAgent SHALL execute agents in this exact order: SourcingAgent, then MatchmakingAgent, then CollaboratorAgent, then DraftingAgent.

**Validates: Requirements 6.2**

### Property 25: Inter-agent data flow

*For any* agent completion within the pipeline, the OrchestratorAgent SHALL pass relevant outputs to subsequent agents.

**Validates: Requirements 6.3**

### Property 26: Orchestrator progress streaming

*For any* orchestration execution, the OrchestratorAgent SHALL stream progress updates as JSON_Line outputs.

**Validates: Requirements 6.5**

### Property 27: Orchestrator completion message

*For any* completed pipeline, the OrchestratorAgent SHALL emit a final JSON_Line with agent="orchestrator", step="Complete", and done=true.

**Validates: Requirements 6.6, 6.7**

### Property 28: Complete result payload

*For any* completed pipeline, the final JSON_Line SHALL include Result_Payload with all required fields: proposalDraft, collaborators, matchScore, matchJustification, complianceChecklist.

**Validates: Requirements 6.8**

### Property 29: No markdown fencing in JSON

*For any* JSON output from the agent service, it SHALL NOT contain markdown fencing (```).

**Validates: Requirements 6.9, 15.1**

### Property 30: AgentCore integration

*For any* agent invocation from Express backend, it SHALL go through AWS AgentCore (not direct HTTP calls).

**Validates: Requirements 7.1, 7.5**


### Property 31: Forge endpoint database queries

*For any* /api/forge/:grantId request, the endpoint SHALL fetch the grant record by grantId AND fetch the full faculty list from the database.

**Validates: Requirements 8.1, 8.2, 17.1, 17.2**

### Property 32: Complete payload construction

*For any* /api/forge/:grantId request, the payload SHALL include all required fields: grantId, grantName, matchCriteria, eligibility, userProfile, facultyList with all specified sub-fields.

**Validates: Requirements 8.3, 17.3, 17.4, 17.5**

### Property 33: SSE proxy streaming

*For any* JSON_Line received from agent service, the Forge endpoint SHALL transform it to SSE format and stream it to the client.

**Validates: Requirements 8.5**

### Property 34: SSE format transformation

*For any* non-final JSON_Line, the SSE message SHALL have format `{ step: "[AgentName]: [step]", done: false }`; for any final JSON_Line, the SSE message SHALL have format `{ step: "Complete", done: true, result: {...} }`.

**Validates: Requirements 8.6, 8.7**

### Property 35: Mock fallback SSE compatibility

*For any* mock step message during fallback, it SHALL use the same SSE message format as real agent output.

**Validates: Requirements 12.3**

### Property 36: Mock step delays

*For any* mock step sequence, there SHALL be realistic delays between steps.

**Validates: Requirements 12.4**

### Property 37: No frontend errors on service failure

*For any* agent service failure, the frontend SHALL receive valid SSE messages (either mock steps or error message), never a broken connection or invalid format.

**Validates: Requirements 12.5**

### Property 38: Model configuration with environment variables

*For any* system startup, if BEDROCK_MODEL_DRAFTING or BEDROCK_MODEL_FAST environment variables are set, the system SHALL use those values; otherwise it SHALL use the default values.

**Validates: Requirements 11.5, 11.6**


### Property 39: JSON output validity

*For any* JSON_Line output from the agent service, it SHALL be valid JSON with properly escaped strings and valid numeric values.

**Validates: Requirements 15.2, 15.3, 15.4, 15.5**

### Property 40: Localhost URLs in local development

*For any* local development environment, all service connections SHALL use localhost URLs.

**Validates: Requirements 16.7**

## Error Handling

### Error Categories

**1. Agent Service Errors**
- Agent service unreachable (connection refused, timeout)
- Invalid response from agent service
- Agent execution failures (model errors, timeout)

**2. AWS Bedrock Errors**
- AccessDeniedException (invalid credentials)
- ThrottlingException (rate limits)
- ValidationException (invalid model parameters)
- ServiceUnavailableException (AWS outage)

**3. Database Errors**
- Grant not found
- Faculty query failures
- Connection errors

**4. Validation Errors**
- Missing required query parameters
- Invalid grantId format
- Malformed request payload

**5. Stream Processing Errors**
- Invalid JSON_Line format
- Incomplete stream
- Connection interruption

### Error Handling Strategy

**Principle:** Graceful degradation with user-friendly messages and comprehensive logging.

#### 1. Agent Service Unreachable

```typescript
try {
  for await (const jsonLine of invokeAgentPipeline(payload)) {
    // Process stream
  }
} catch (error) {
  console.warn('Agent service unreachable, falling back to mock steps:', error);
  await sendMockSteps(res, grant, role, year, program);
}
```

**Behavior:**
- Log warning with error details
- Fall back to mock steps automatically
- Frontend receives valid SSE stream
- No user-facing error


#### 2. Grant Not Found

```typescript
const grant = await storage.getGrantById(parseInt(grantId));
if (!grant) {
  res.write(`data: ${JSON.stringify({
    step: "Grant not found",
    done: true,
    error: true
  })}\n\n`);
  return res.end();
}
```

**Behavior:**
- Return error SSE message immediately
- Close connection cleanly
- Log error server-side

#### 3. AWS Bedrock Errors

```python
# In agent service
try:
    response = await bedrock_model.invoke(prompt)
except AccessDeniedException:
    logger.error("AWS Bedrock access denied - check credentials")
    yield {
        "agent": agent_name,
        "step": "Service configuration error",
        "output": None,
        "done": True
    }
except ThrottlingException:
    logger.warning("AWS Bedrock throttling - rate limit exceeded")
    yield {
        "agent": agent_name,
        "step": "Service temporarily busy, please retry",
        "output": None,
        "done": True
    }
```

**Behavior:**
- Log detailed error server-side
- Return user-friendly message
- Set done=true to signal completion
- Express backend forwards as SSE

#### 4. Invalid JSON_Line

```python
def sanitize_json_line(line: dict) -> dict:
    """Ensure JSON_Line is valid and properly formatted"""
    sanitized = {
        "agent": str(line.get("agent", "unknown")),
        "step": str(line.get("step", "Processing...")),
        "output": line.get("output"),
        "done": bool(line.get("done", False))
    }
    
    # Validate JSON serialization
    try:
        json.dumps(sanitized)
        return sanitized
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization failed: {e}")
        return {
            "agent": "system",
            "step": "Processing error",
            "output": None,
            "done": True
        }
```

**Behavior:**
- Validate before streaming
- Sanitize invalid data
- Log errors for debugging
- Never send malformed JSON to client


#### 5. Missing Environment Variables

```python
# In agent service startup
required_vars = ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    logger.error(f"Missing required environment variables: {missing}")
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
```

```typescript
// In Express backend startup
const required = ["DATABASE_URL", "AGENT_SERVICE_URL", "AWS_REGION"];
const missing = required.filter(v => !process.env[v]);

if (missing.length > 0) {
  console.error(`Missing required environment variables: ${missing.join(', ')}`);
  process.exit(1);
}
```

**Behavior:**
- Fail fast at startup
- Clear error messages
- Prevent partial initialization
- Exit with non-zero code

### Logging Strategy

**Server-Side Logging:**
```python
import logging

logger = logging.getLogger("fundingforge.agents")
logger.setLevel(logging.INFO)

# Log all agent invocations
logger.info(f"Agent invocation: {agent_name}", extra={
    "grant_id": request.grantId,
    "user_profile": request.userProfile
})

# Log errors with context
logger.error(f"Agent execution failed: {agent_name}", extra={
    "error": str(error),
    "grant_id": request.grantId
}, exc_info=True)
```

**Express Backend Logging:**
```typescript
// Log agent service calls
console.log(`[AgentCore] Invoking pipeline for grant ${grantId}`);

// Log fallback scenarios
console.warn(`[AgentCore] Service unreachable, using mock fallback`);

// Log errors
console.error(`[Forge] Error processing request:`, {
  grantId,
  error: error.message
});
```

### Recovery Mechanisms

**1. Automatic Retry (Agent Service)**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def invoke_bedrock_with_retry(model, prompt):
    return await model.invoke(prompt)
```

**2. Circuit Breaker (Express Backend)**
```typescript
let agentServiceFailures = 0;
const FAILURE_THRESHOLD = 5;
const RESET_TIMEOUT = 60000; // 1 minute

async function invokeWithCircuitBreaker(payload) {
  if (agentServiceFailures >= FAILURE_THRESHOLD) {
    console.warn('Circuit breaker open, using mock fallback');
    throw new Error('Circuit breaker open');
  }
  
  try {
    const result = await invokeAgentPipeline(payload);
    agentServiceFailures = 0; // Reset on success
    return result;
  } catch (error) {
    agentServiceFailures++;
    setTimeout(() => { agentServiceFailures = 0; }, RESET_TIMEOUT);
    throw error;
  }
}
```


## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples and edge cases (grant not found, specific model IDs)
- Integration points between components (Express ↔ AgentCore ↔ Agent Service)
- Error conditions with mocked responses (AWS errors, invalid JSON)
- Environment validation with specific missing variables

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs (JSON_Line format, SSE transformation)
- Comprehensive input coverage through randomization (various grant data, user profiles)
- Agent execution order and data flow across varied scenarios
- Payload construction with random valid inputs

### Property-Based Testing Configuration

**Library Selection:**
- TypeScript/Node.js: Use `fast-check` for Express backend tests
- Python: Use `hypothesis` for agent service tests
- Minimum 100 iterations per property test
- Each test references its design document property

**Test Tagging Format:**
```typescript
// Feature: aws-bedrock-backend-integration, Property 31: Forge endpoint database queries
test('forge endpoint fetches grant and faculty for any valid grantId', async () => {
  await fc.assert(
    fc.asyncProperty(fc.integer({ min: 1, max: 1000 }), async (grantId) => {
      // Test implementation
    }),
    { numRuns: 100 }
  );
});
```

```python
# Feature: aws-bedrock-backend-integration, Property 7: JSON_Line streaming format
@given(agent_name=st.sampled_from(["sourcing", "matchmaking", "collaborator", "drafting"]))
@settings(max_examples=100)
def test_json_line_format(agent_name):
    # Test implementation
    pass
```

### Unit Test Coverage

#### Agent Service Tests

**SourcingAgent:**
- ✓ Uses correct Haiku model ID (example test)
- ✓ Extracts experience from sample profile (example test)
- ✓ Returns structured data with required fields (example test)
- ✓ Emits done=true on completion (example test)

**MatchmakingAgent:**
- ✓ Uses correct Haiku model ID (example test)
- ✓ Returns match score in range [0, 100] (example test)
- ✓ Includes compliance checklist with RAMP item (example test)
- ✓ Includes compliance checklist with COI item (example test)
- ✓ Includes compliance checklist with IRB item (example test)
- ✓ Includes compliance checklist with Policy item (example test)

**CollaboratorAgent:**
- ✓ Uses correct Haiku model ID (example test)
- ✓ Returns at most 3 collaborators (example test)
- ✓ Each collaborator has relevance score (example test)

**DraftingAgent:**
- ✓ Uses correct Sonnet model ID (example test)
- ✓ Generates proposal with section headers (example test)
- ✓ Proposal is between 300-500 words (example test)

**OrchestratorAgent:**
- ✓ Executes all 4 agents in correct order (example test)
- ✓ Final message has agent="orchestrator" (example test)
- ✓ Final message includes complete Result_Payload (example test)


#### Express Backend Tests

**Forge Endpoint:**
- ✓ Fetches grant by grantId (example test)
- ✓ Fetches faculty list (example test)
- ✓ Returns error SSE for invalid grantId (edge case)
- ✓ Falls back to mock steps when agent service unreachable (edge case)
- ✓ Logs console.warn on fallback (example test)
- ✓ Transforms JSON_Line to SSE format (example test)

**AgentCore Integration:**
- ✓ Uses AgentCore client for invocation (example test)
- ✓ Does not make direct HTTP calls (example test)
- ✓ Uses AGENT_SERVICE_URL from environment (example test)

**Environment Validation:**
- ✓ Exits on missing DATABASE_URL (edge case)
- ✓ Exits on missing AGENT_SERVICE_URL (edge case)
- ✓ Exits on missing AWS_REGION (edge case)
- ✓ Uses default model IDs when env vars not set (example test)
- ✓ Uses custom model IDs when env vars set (example test)

**Schema Validation:**
- ✓ forgeStreamChunkSchema includes result field (example test)
- ✓ result.proposalDraft is z.string() (example test)
- ✓ result.collaborators is array with correct structure (example test)
- ✓ result.matchScore is z.number() (example test)
- ✓ result.complianceChecklist has correct enum values (example test)

### Property-Based Test Coverage

#### Property 2: Request payload validation
```python
# Feature: aws-bedrock-backend-integration, Property 2: Request payload validation
@given(
    grant_id=st.integers(min_value=1),
    grant_name=st.text(min_size=1),
    match_criteria=st.text(),
    eligibility=st.text(),
    role=st.text(min_size=1),
    year=st.text(min_size=1),
    program=st.text(min_size=1)
)
@settings(max_examples=100)
def test_valid_payload_accepted(grant_id, grant_name, match_criteria, eligibility, role, year, program):
    payload = {
        "grantId": grant_id,
        "grantName": grant_name,
        "matchCriteria": match_criteria,
        "eligibility": eligibility,
        "userProfile": {"role": role, "year": year, "program": program},
        "facultyList": []
    }
    response = client.post("/invoke", json=payload)
    assert response.status_code == 200
```

#### Property 3: AgentCore URL configuration
```typescript
// Feature: aws-bedrock-backend-integration, Property 3: AgentCore URL configuration
fc.assert(
  fc.property(
    fc.webUrl(),
    (url) => {
      process.env.AGENT_SERVICE_URL = url;
      const client = createAgentCoreClient();
      expect(client.config.endpoint).toBe(url);
    }
  ),
  { numRuns: 100 }
);
```


#### Property 7: JSON_Line streaming format
```python
# Feature: aws-bedrock-backend-integration, Property 7: JSON_Line streaming format
@given(
    agent_name=st.sampled_from(["sourcing", "matchmaking", "collaborator", "drafting"]),
    step_text=st.text(min_size=1),
    done_flag=st.booleans()
)
@settings(max_examples=100)
def test_json_line_has_required_fields(agent_name, step_text, done_flag):
    json_line = create_json_line(agent_name, step_text, None, done_flag)
    assert "agent" in json_line
    assert "step" in json_line
    assert "output" in json_line
    assert "done" in json_line
    assert json_line["agent"] == agent_name
    assert json_line["step"] == step_text
    assert json_line["done"] == done_flag
```

#### Property 11: Match score range validation
```python
# Feature: aws-bedrock-backend-integration, Property 11: Match score range validation
@given(
    user_profile=st.fixed_dictionaries({
        "role": st.text(min_size=1),
        "year": st.text(min_size=1),
        "program": st.text(min_size=1)
    }),
    match_criteria=st.text()
)
@settings(max_examples=100)
async def test_match_score_in_range(user_profile, match_criteria):
    result = await matchmaking_agent.run({
        "userProfile": user_profile,
        "matchCriteria": match_criteria
    })
    assert 0 <= result["matchScore"] <= 100
```

#### Property 16: Proposal word count constraint
```python
# Feature: aws-bedrock-backend-integration, Property 16: Proposal word count constraint
@given(
    grant_name=st.text(min_size=1),
    match_criteria=st.text(),
    eligibility=st.text()
)
@settings(max_examples=100)
async def test_proposal_word_count(grant_name, match_criteria, eligibility):
    result = await drafting_agent.run({
        "grantName": grant_name,
        "matchCriteria": match_criteria,
        "eligibility": eligibility
    })
    word_count = len(result["proposalDraft"].split())
    assert 300 <= word_count <= 500
```

#### Property 21: Top collaborators limit
```python
# Feature: aws-bedrock-backend-integration, Property 21: Top collaborators limit
@given(
    faculty_list=st.lists(
        st.fixed_dictionaries({
            "name": st.text(min_size=1),
            "department": st.text(min_size=1),
            "expertise": st.text(min_size=1)
        }),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
async def test_collaborator_limit(faculty_list):
    result = await collaborator_agent.run({"facultyList": faculty_list})
    assert len(result["collaborators"]) <= 3
```


#### Property 24: Agent execution order
```python
# Feature: aws-bedrock-backend-integration, Property 24: Agent execution order
@given(
    grant_id=st.integers(min_value=1),
    grant_name=st.text(min_size=1)
)
@settings(max_examples=100)
async def test_agent_execution_order(grant_id, grant_name):
    execution_log = []
    
    async for json_line in orchestrator_agent.run({
        "grantId": grant_id,
        "grantName": grant_name
    }):
        if json_line["agent"] != "orchestrator":
            execution_log.append(json_line["agent"])
    
    # Verify order
    expected_order = ["sourcing", "matchmaking", "collaborator", "drafting"]
    actual_order = [agent for agent in execution_log if agent in expected_order]
    
    # Check that each agent appears and in correct order
    assert actual_order == expected_order[:len(actual_order)]
```

#### Property 31: Forge endpoint database queries
```typescript
// Feature: aws-bedrock-backend-integration, Property 31: Forge endpoint database queries
fc.assert(
  fc.asyncProperty(
    fc.integer({ min: 1, max: 1000 }),
    async (grantId) => {
      const mockStorage = {
        getGrantById: jest.fn().mockResolvedValue({ id: grantId, name: "Test Grant" }),
        getFaculty: jest.fn().mockResolvedValue([])
      };
      
      await forgeEndpoint(grantId, mockStorage);
      
      expect(mockStorage.getGrantById).toHaveBeenCalledWith(grantId);
      expect(mockStorage.getFaculty).toHaveBeenCalled();
    }
  ),
  { numRuns: 100 }
);
```

#### Property 32: Complete payload construction
```typescript
// Feature: aws-bedrock-backend-integration, Property 32: Complete payload construction
fc.assert(
  fc.asyncProperty(
    fc.record({
      grantId: fc.integer({ min: 1 }),
      grantName: fc.string({ minLength: 1 }),
      matchCriteria: fc.string(),
      eligibility: fc.string(),
      role: fc.string({ minLength: 1 }),
      year: fc.string({ minLength: 1 }),
      program: fc.string({ minLength: 1 })
    }),
    async (data) => {
      const payload = buildInvokePayload(data);
      
      expect(payload).toHaveProperty("grantId", data.grantId);
      expect(payload).toHaveProperty("grantName", data.grantName);
      expect(payload).toHaveProperty("matchCriteria", data.matchCriteria);
      expect(payload).toHaveProperty("eligibility", data.eligibility);
      expect(payload).toHaveProperty("userProfile");
      expect(payload.userProfile).toHaveProperty("role", data.role);
      expect(payload.userProfile).toHaveProperty("year", data.year);
      expect(payload.userProfile).toHaveProperty("program", data.program);
      expect(payload).toHaveProperty("facultyList");
      expect(Array.isArray(payload.facultyList)).toBe(true);
    }
  ),
  { numRuns: 100 }
);
```


#### Property 34: SSE format transformation
```typescript
// Feature: aws-bedrock-backend-integration, Property 34: SSE format transformation
fc.assert(
  fc.asyncProperty(
    fc.oneof(
      // Non-final JSON_Line
      fc.record({
        agent: fc.constantFrom("sourcing", "matchmaking", "collaborator", "drafting"),
        step: fc.string({ minLength: 1 }),
        output: fc.constant(null),
        done: fc.constant(false)
      }),
      // Final JSON_Line
      fc.record({
        agent: fc.constant("orchestrator"),
        step: fc.constant("Complete"),
        output: fc.object(),
        done: fc.constant(true)
      })
    ),
    async (jsonLine) => {
      const sseMessage = transformToSSE(jsonLine);
      
      if (jsonLine.done) {
        expect(sseMessage.step).toBe("Complete");
        expect(sseMessage.done).toBe(true);
        expect(sseMessage).toHaveProperty("result");
      } else {
        expect(sseMessage.step).toContain(jsonLine.agent);
        expect(sseMessage.step).toContain(jsonLine.step);
        expect(sseMessage.done).toBe(false);
        expect(sseMessage).not.toHaveProperty("result");
      }
    }
  ),
  { numRuns: 100 }
);
```

#### Property 39: JSON output validity
```python
# Feature: aws-bedrock-backend-integration, Property 39: JSON output validity
@given(
    agent_name=st.text(min_size=1),
    step_text=st.text(),
    output_data=st.one_of(st.none(), st.dictionaries(st.text(), st.text()))
)
@settings(max_examples=100)
def test_json_line_is_valid_json(agent_name, step_text, output_data):
    json_line = {
        "agent": agent_name,
        "step": step_text,
        "output": output_data,
        "done": False
    }
    
    # Should be serializable to JSON
    json_str = json.dumps(json_line)
    
    # Should be deserializable
    parsed = json.loads(json_str)
    
    # Should match original
    assert parsed["agent"] == agent_name
    assert parsed["step"] == step_text
```

### Test Environment Setup

**Mocking Strategy:**
- Mock AWS Bedrock SDK for agent tests
- Mock AgentCore client for Express tests
- Use test doubles for storage layer
- Mock environment variables for validation tests
- Use in-memory SSE capture for endpoint tests

**Test Data:**
- Generate realistic grant records with varied criteria
- Create diverse faculty profiles with different expertise
- Use varied user profiles (different roles, years, programs)
- Include edge cases (empty strings, very long inputs, special characters)

### Integration Testing

**End-to-End Flow:**
1. Start all services (Express, AgentCore, Agent Service)
2. Seed test database with grants and faculty
3. Make SSE request to /api/forge/:grantId
4. Verify complete flow from request to completion
5. Validate SSE message sequence
6. Confirm result payload structure
7. Verify all 5 agents executed in order

**Performance Testing:**
- Measure streaming latency (time to first token)
- Test concurrent requests (multiple users)
- Verify memory usage during long streams
- Validate connection cleanup
- Test agent service under load


## Implementation Notes

### Dependency Installation

**Agent Service (Python):**
```txt
# agent-service/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
strands-agents==0.5.0
strands-agents-tools==0.3.0
boto3==1.34.0
pydantic==2.5.0
python-dotenv==1.0.0
tenacity==8.2.3
```

**Express Backend (TypeScript):**
```json
{
  "dependencies": {
    "@aws-sdk/client-agentcore": "^3.500.0",
    "dotenv": "^16.4.5"
  },
  "devDependencies": {
    "fast-check": "^3.15.0",
    "@types/node": "^20.11.0"
  }
}
```

### File Structure

```
fundingforge/
├── agent-service/
│   ├── main.py                 # FastAPI app with /invoke endpoint
│   ├── agents/
│   │   ├── sourcing.py         # SourcingAgent implementation
│   │   ├── matchmaking.py      # MatchmakingAgent implementation
│   │   ├── collaborator.py     # CollaboratorAgent implementation
│   │   ├── drafting.py         # DraftingAgent implementation
│   │   └── orchestrator.py     # OrchestratorAgent implementation
│   ├── models.py               # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── notebooks/
│       ├── 01_sourcing_agent.ipynb
│       ├── 02_matchmaking_agent.ipynb
│       ├── 03_collaborator_agent.ipynb
│       ├── 04_drafting_agent.ipynb
│       ├── 05_orchestrator_agent.ipynb
│       └── 06_full_pipeline.ipynb
├── server/
│   ├── agentcore-client.ts    # AgentCore integration
│   ├── routes.ts               # Updated /api/forge endpoint
│   ├── index.ts                # Environment validation
│   └── storage.ts              # Existing storage layer
├── shared/
│   └── routes.ts               # Updated schema with result field
└── .env.example
```

### Environment Variables

**Agent Service (.env):**
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_DRAFTING=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_FAST=anthropic.claude-haiku-4-5-20251001-v1:0
PORT=8001
```

**Express Backend (.env):**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fundingforge
AGENT_SERVICE_URL=http://localhost:8001
AGENTCORE_ENDPOINT=http://localhost:8000
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Local Development Setup

**1. Start PostgreSQL:**
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```

**2. Start Agent Service:**
```bash
cd agent-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload
```

**3. Start AWS AgentCore (Local):**
```bash
# Follow AWS AgentCore local setup documentation
agentcore start --port 8000
```

**4. Start Express Backend:**
```bash
npm install
npm run db:push  # Initialize database
npm run dev
```

**5. Access Application:**
- Frontend: http://localhost:5000
- Agent Service: http://localhost:8001/docs (FastAPI Swagger UI)
- AgentCore: http://localhost:8000


### Jupyter Notebook Structure

Each notebook follows this pattern:

**01_sourcing_agent.ipynb:**
```python
# Cell 1: Install dependencies
!pip install strands-agents strands-agents-tools boto3

# Cell 2: Import and configure
from strands import Agent
from strands.models import BedrockModel
import os

os.environ["AWS_REGION"] = "us-east-1"

# Cell 3: Create model
fast_model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# Cell 4: Define system prompt
system_prompt = """
You are the SourcingAgent for FundingForge...
"""

# Cell 5: Create agent
sourcing_agent = Agent(model=fast_model, system_prompt=system_prompt)

# Cell 6: Test with sample data
sample_profile = {
    "role": "PhD Student",
    "year": "2024",
    "program": "Computer Science"
}

# Cell 7: Run and display results
async for output in sourcing_agent.run(sample_profile):
    print(output)

# Cell 8: Export function
def create_sourcing_agent():
    return Agent(model=fast_model, system_prompt=system_prompt)
```

**06_full_pipeline.ipynb:**
```python
# Imports all agent functions from previous notebooks
# Chains them together
# Simulates complete /invoke flow
# Displays streaming output
# Validates final Result_Payload structure
```

### AWS Permissions

**IAM Policy for Bedrock Access:**
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
      "Resource": [
        "arn:aws:bedrock:*:*:model/anthropic.claude-3-haiku-*",
        "arn:aws:bedrock:*:*:model/anthropic.claude-sonnet-*"
      ]
    }
  ]
}
```

**IAM Policy for AgentCore:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "agentcore:InvokeAgent",
        "agentcore:GetAgent",
        "agentcore:ListAgents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Deployment Considerations

**Cost Estimation:**
- Claude Haiku: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- Claude Sonnet: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Typical pipeline:
  - SourcingAgent: 200 input + 300 output tokens
  - MatchmakingAgent: 400 input + 500 output tokens
  - CollaboratorAgent: 300 input + 200 output tokens
  - DraftingAgent: 600 input + 400 output tokens (Sonnet)
- Estimated cost per proposal: ~$0.015

**Scaling Considerations:**
- Agent service can be horizontally scaled
- AgentCore handles load balancing
- Database connection pooling required
- Consider caching for repeated grant queries

**Monitoring:**
- Track agent execution times per stage
- Monitor Bedrock API latency and errors
- Alert on high error rates or timeouts
- Log all agent invocations for debugging
- Track cost per proposal generation


### Security Best Practices

**1. Credential Management:**
- Never commit credentials to version control
- Use environment variables for all secrets
- Rotate AWS credentials regularly
- Use IAM roles in production (avoid access keys)
- Implement least-privilege IAM policies

**2. Input Validation:**
- Validate all user inputs before passing to agents
- Sanitize grant criteria and eligibility text
- Limit input lengths to prevent abuse
- Validate grantId is positive integer
- Escape special characters in JSON

**3. Output Sanitization:**
- Validate all agent outputs before streaming
- Remove any potentially sensitive information
- Ensure JSON is properly formatted
- Filter markdown fencing from responses
- Validate numeric ranges (match scores, relevance scores)

**4. Network Security:**
- Use HTTPS for all external communications
- Implement rate limiting on /api/forge endpoint
- Use VPC for agent service in production
- Restrict AgentCore access to authorized services
- Implement request timeout limits

**5. Error Handling:**
- Never expose AWS error details to clients
- Log detailed errors server-side only
- Sanitize all error messages
- Implement circuit breakers for external services
- Graceful degradation on failures

### Performance Optimization

**1. Streaming Benefits:**
- Reduces time-to-first-token for better UX
- Allows client to display partial results
- Prevents timeout on long-running requests
- Enables real-time progress updates

**2. Caching Strategy (Future Enhancement):**
- Cache grant records (TTL: 1 hour)
- Cache faculty list (TTL: 24 hours)
- Consider caching proposal results for identical inputs
- Use Redis for distributed caching
- Invalidate cache on data updates

**3. Database Optimization:**
- Index grants table on id
- Index faculty table on department and expertise
- Use connection pooling
- Implement read replicas for high load
- Cache frequently accessed queries

**4. Agent Optimization:**
- Use Haiku for fast operations (sourcing, matching, collaborator)
- Reserve Sonnet for quality-critical operations (drafting)
- Implement request batching where possible
- Monitor token usage and optimize prompts
- Consider prompt caching for repeated patterns

### Backward Compatibility

**Preserved Contracts:**
- ✓ GET /api/grants returns Grant[]
- ✓ GET /api/faculty returns Faculty[]
- ✓ GET /api/forge/:grantId uses SSE
- ✓ SSE message format unchanged
- ✓ Database schema unchanged
- ✓ Frontend code requires no modifications

**Migration Path:**
1. Deploy agent service
2. Deploy AgentCore configuration
3. Update Express backend with AgentCore integration
4. Test /api/forge endpoint
5. Monitor for errors
6. No frontend deployment required

**Rollback Strategy:**
- Keep mock fallback logic in place
- Can disable agent service without breaking frontend
- Environment variable controls agent service usage
- Database remains unchanged for easy rollback

## Conclusion

This design transforms FundingForge from a mock system to a production-ready multi-agent AI pipeline powered by AWS Bedrock. The architecture introduces five specialized agents orchestrated through AWS AgentCore, while maintaining complete backward compatibility with the existing frontend.

Key design decisions:
- **Five-Agent Architecture:** Specialized agents (Sourcing, Matchmaking, Collaborator, Drafting, Orchestrator) with clear responsibilities
- **AWS AgentCore Integration:** Managed agent lifecycle and communication layer
- **Dual Model Strategy:** Haiku for speed (3 agents), Sonnet for quality (drafting)
- **Graceful Degradation:** Automatic fallback to mock steps ensures zero downtime
- **Local Development:** Full stack runs locally for rapid iteration
- **Comprehensive Testing:** Property-based tests validate universal properties across all inputs
- **Security First:** Multi-layer sanitization, validation, and error handling

The implementation follows FastAPI and Express.js best practices, uses the Strands Agents SDK for agent construction, and provides Jupyter notebooks for isolated agent testing and prototyping.

