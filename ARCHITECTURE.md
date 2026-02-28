# Architecture Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                      (React Frontend)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/SSE
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Express Backend (Node.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Routes     │  │   Storage    │  │  AgentCore   │         │
│  │  /api/forge  │──│   (Drizzle)  │  │    Client    │         │
│  └──────────────┘  └──────────────┘  └──────┬───────┘         │
└────────────────────────────────────────────────┼────────────────┘
                                                 │ HTTP
                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AWS AgentCore (Local)                          │
│                  (Agent Lifecycle Manager)                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Python Agent Service (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  OrchestratorAgent                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │  Sourcing  │→ │ Matchmaking│→ │Collaborator│→       │  │
│  │  │   Agent    │  │   Agent    │  │   Agent    │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  │                                                          │  │
│  │  ┌────────────┐                                         │  │
│  │  │  Drafting  │                                         │  │
│  │  │   Agent    │                                         │  │
│  │  └────────────┘                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ AWS SDK
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Bedrock                               │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  Claude Haiku    │         │  Claude Sonnet   │             │
│  │  (Fast, 3 agents)│         │ (Quality, Draft) │             │
│  └──────────────────┘         └──────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Flow

```
1. User selects grant and enters profile
   ↓
2. Frontend sends SSE request to /api/forge/:grantId
   ↓
3. Express backend:
   - Fetches grant from PostgreSQL
   - Fetches faculty list from PostgreSQL
   - Builds InvokePayload
   ↓
4. Express sends payload to AgentCore
   ↓
5. AgentCore forwards to Agent Service
   ↓
6. OrchestratorAgent executes pipeline:
   
   SourcingAgent:
   - Input: userProfile
   - Process: Extract CV data, publications, expertise
   - Output: Structured user data
   - Model: Claude Haiku
   
   MatchmakingAgent:
   - Input: userProfile, sourcedData, matchCriteria
   - Process: Analyze fit + check compliance (RAMP, COI, IRB, Policy)
   - Output: matchScore, matchJustification, complianceChecklist
   - Model: Claude Haiku
   
   CollaboratorAgent:
   - Input: facultyList, matchCriteria, userProfile
   - Process: Match faculty by expertise
   - Output: Top 3 faculty with relevance scores
   - Model: Claude Haiku
   
   DraftingAgent:
   - Input: grantName, matchCriteria, matchJustification, collaborators
   - Process: Generate proposal narrative (300-500 words)
   - Output: proposalDraft with section headers
   - Model: Claude Sonnet (highest quality)
   
   ↓
7. Each agent streams JSON_Line progress updates
   ↓
8. AgentCore streams back to Express
   ↓
9. Express transforms JSON_Line to SSE format
   ↓
10. Frontend displays real-time updates
    ↓
11. Final result includes complete proposal package
```

### Response Flow (SSE)

```
Agent Service          Express Backend         Frontend
     │                       │                     │
     │ JSON_Line             │                     │
     │ {"agent":"sourcing",  │                     │
     │  "step":"Extracting", │                     │
     │  "done":false}        │                     │
     ├──────────────────────>│                     │
     │                       │ SSE                 │
     │                       │ data: {"step":      │
     │                       │  "sourcing:         │
     │                       │   Extracting",      │
     │                       │  "done":false}      │
     │                       ├────────────────────>│
     │                       │                     │ Display: "Extracting..."
     │                       │                     │
     │ JSON_Line             │                     │
     │ {"agent":"orchestrator│                     │
     │  "step":"Complete",   │                     │
     │  "output":{...},      │                     │
     │  "done":true}         │                     │
     ├──────────────────────>│                     │
     │                       │ SSE                 │
     │                       │ data: {"step":      │
     │                       │  "Complete",        │
     │                       │  "done":true,       │
     │                       │  "result":{...}}    │
     │                       ├────────────────────>│
     │                       │                     │ Display: Final result
```

## Component Responsibilities

### Frontend (React)

**Responsibilities:**
- User interface and interaction
- Grant selection and profile input
- SSE connection management
- Real-time progress display
- Result visualization

**Key Files:**
- `client/src/pages/Home.tsx` - Main page
- `client/src/components/SelectionPortal.tsx` - Grant selection
- `client/src/components/DiscoveryDashboard.tsx` - Results display
- `client/src/hooks/use-forge-stream.ts` - SSE hook

### Express Backend (Node.js)

**Responsibilities:**
- REST API endpoints
- Database queries (grants, faculty)
- AgentCore integration
- SSE proxy and transformation
- Graceful degradation (mock fallback)
- Session management

**Key Files:**
- `server/routes.ts` - API routes
- `server/storage.ts` - Database layer
- `server/agentcore-client.ts` - AgentCore integration
- `server/index.ts` - Server entry point

### AWS AgentCore

**Responsibilities:**
- Agent lifecycle management
- Communication routing
- Health monitoring
- Load balancing (production)

**Configuration:**
- Endpoint: http://localhost:8000 (local)
- Manages connection to agent service

### Python Agent Service (FastAPI)

**Responsibilities:**
- Multi-agent orchestration
- Bedrock model invocation
- JSON_Line streaming
- Error handling and retry logic
- Input validation

**Key Files:**
- `agent-service/main.py` - FastAPI app
- `agent-service/models.py` - Pydantic models
- `agent-service/agents/orchestrator.py` - Pipeline coordinator
- `agent-service/agents/sourcing.py` - User data extraction
- `agent-service/agents/matchmaking.py` - Fit analysis + compliance
- `agent-service/agents/collaborator.py` - Faculty matching
- `agent-service/agents/drafting.py` - Proposal generation

### AWS Bedrock

**Responsibilities:**
- Foundation model inference
- Token-based billing
- Rate limiting and throttling

**Models Used:**
- **Claude Haiku** (anthropic.claude-haiku-4-5-20251001-v1:0)
  - Fast, cost-effective
  - Used for: Sourcing, Matchmaking, Collaborator
  - Cost: ~$0.25/1M input, ~$1.25/1M output
  
- **Claude Sonnet** (anthropic.claude-sonnet-4-6)
  - Highest quality
  - Used for: Drafting (proposal generation)
  - Cost: ~$3/1M input, ~$15/1M output

## Database Schema

### Tables

**grants**
- id (serial, primary key)
- name (text)
- targetAudience (text)
- eligibility (text)
- matchCriteria (text)
- internalDeadline (text)

**faculty**
- id (serial, primary key)
- name (text)
- department (text)
- expertise (text)
- imageUrl (text)
- bio (text, nullable)

## API Contracts

### REST Endpoints

**GET /api/grants**
- Response: `Grant[]`
- Purpose: List all available grants

**GET /api/faculty**
- Response: `Faculty[]`
- Purpose: List all faculty members

### SSE Endpoint

**GET /api/forge/:grantId?role=X&year=Y&program=Z**
- Response: Server-Sent Events stream
- Chunk Format:
  ```typescript
  {
    step: string;           // Progress message
    done: boolean;          // Completion flag
    error?: boolean;        // Error flag
    result?: {              // Final result (when done=true)
      proposalDraft: string;
      collaborators: Array<{
        name: string;
        department: string;
        expertise: string;
        relevanceScore: number;
      }>;
      matchScore: number;   // 0-100
      matchJustification: string;
      complianceChecklist: Array<{
        task: string;
        category: "RAMP" | "COI" | "IRB" | "Policy";
        status: "green" | "yellow" | "red";
      }>;
    };
  }
  ```

### Agent Service Endpoint

**POST /invoke**
- Request:
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
- Response: Newline-delimited JSON stream
- Format:
  ```typescript
  {
    agent: string;
    step: string;
    output: any;
    done: boolean;
  }
  ```

## Error Handling Strategy

### Graceful Degradation

```
Agent Service Unreachable
    ↓
Express Backend Detects Failure
    ↓
Log Warning to Console
    ↓
Fall Back to Mock Steps
    ↓
Send Mock SSE Messages
    ↓
Frontend Receives Valid Stream
    ↓
User Experience Uninterrupted
```

### Error Types and Responses

| Error Type | Handler | Response |
|------------|---------|----------|
| Agent service down | Express backend | Mock fallback |
| Grant not found | Express backend | Error SSE message |
| AWS AccessDenied | Agent service | User-friendly error |
| AWS Throttling | Agent service | Retry with backoff |
| Invalid JSON_Line | Agent service | Sanitize and log |
| Database error | Express backend | Error SSE message |

## Security Architecture

### Authentication & Authorization

```
User Request
    ↓
Express Session Middleware
    ↓
Route Handler
    ↓
Database Query (with user context)
    ↓
Agent Service (no user data stored)
    ↓
AWS Bedrock (ephemeral processing)
```

### Data Flow Security

1. **Input Validation**
   - Express: Validate query parameters
   - Agent Service: Validate request payload with Pydantic
   
2. **Output Sanitization**
   - Agent Service: Validate JSON_Line format
   - Express: Transform and validate SSE messages
   
3. **Credential Management**
   - Environment variables only
   - Never in code or version control
   - IAM roles in production

4. **Network Security**
   - HTTPS in production
   - Rate limiting on public endpoints
   - VPC for agent service (production)

## Deployment Architecture

### Local Development

```
Developer Machine
├── PostgreSQL (Docker, port 5432)
├── Agent Service (Python, port 8001)
├── AgentCore (Local, port 8000)
└── Express Backend (Node.js, port 5000)
    └── Frontend (Vite dev server)
```

### Production (Recommended)

```
Load Balancer (HTTPS)
    ↓
Express Backend (Multiple instances)
    ├── PostgreSQL (RDS/Managed)
    ├── AgentCore (AWS Service)
    └── Agent Service (ECS/Lambda)
        └── AWS Bedrock
```

## Performance Characteristics

### Latency

- **Time to First Token**: ~2-3 seconds
- **SourcingAgent**: ~3-5 seconds
- **MatchmakingAgent**: ~4-6 seconds
- **CollaboratorAgent**: ~2-4 seconds
- **DraftingAgent**: ~8-12 seconds (Sonnet, highest quality)
- **Total Pipeline**: ~20-30 seconds

### Throughput

- **Concurrent Users**: Limited by Bedrock quotas
- **Requests per Second**: ~10-20 (with proper scaling)
- **Database Queries**: Cached for performance

### Cost

- **Per Proposal**: ~$0.015
- **1000 Proposals**: ~$15
- **Monthly (1000 proposals)**: ~$15 + infrastructure

## Monitoring & Observability

### Metrics to Track

1. **Agent Service**
   - Request count per agent
   - Average execution time per agent
   - Error rate per agent
   - Token usage per agent

2. **Express Backend**
   - SSE connection count
   - Request latency
   - Database query time
   - Fallback activation rate

3. **AWS Bedrock**
   - API call count
   - Throttling events
   - Token consumption
   - Cost per day

### Logging Strategy

```
Agent Service → CloudWatch Logs
Express Backend → Application Logs
Database → Query Logs
AWS Bedrock → CloudWatch Metrics
```

## Scalability

### Horizontal Scaling

- **Agent Service**: Stateless, can scale horizontally
- **Express Backend**: Stateless, can scale horizontally
- **Database**: Read replicas for queries
- **AgentCore**: Handles load balancing

### Vertical Scaling

- **Agent Service**: More CPU for faster processing
- **Database**: More memory for caching
- **Express Backend**: More memory for concurrent connections

---

**This architecture provides a robust, scalable, and maintainable foundation for AI-powered grant proposal generation.**
