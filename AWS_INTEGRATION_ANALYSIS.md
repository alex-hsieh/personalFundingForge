# AWS Integration Analysis for FundingForge

## Executive Summary

This document provides a comprehensive analysis of how to properly integrate AWS services into the FundingForge grant proposal generation platform. Based on AWS documentation and best practices, we outline three architectural approaches with varying levels of AWS service integration.

## Current Architecture Issues

### Misunderstanding: "AWS AgentCore as Middleware"

The original spec incorrectly describes AWS AgentCore as a communication layer between Express and the agent service. **This is incorrect.**

**What AgentCore Actually Is:**
- **Amazon Bedrock AgentCore** is a **serverless runtime platform** for deploying and hosting AI agents
- Similar to AWS Fargate (for containers) or AWS Lambda (for functions)
- It's where you **deploy your agents**, not a proxy/middleware service
- Provides: session isolation, memory management, observability, identity management

**What It's NOT:**
- NOT a client SDK
- NOT a proxy between Express and FastAPI
- NOT required for using Strands Agents SDK

---

## Three Architectural Approaches

### **Option 1: Current Architecture + Knowledge Base (Recommended for MVP)**

**Keep:** FastAPI service, Strands Agents, Direct HTTP
**Add:** Knowledge Bases for Amazon Bedrock with S3

```
┌─────────────┐
│   Express   │
│   Backend   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│  FastAPI Agent Service          │
│  ┌──────────────────────────┐  │
│  │  Strands Agents          │  │
│  │  - SourcingAgent         │  │
│  │  - MatchmakingAgent      │  │
│  │  - CollaboratorAgent     │  │
│  │  - DraftingAgent         │  │
│  │  - OrchestratorAgent     │  │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌─────────────┐  ┌──────────────────────┐
│   Bedrock   │  │  Knowledge Base      │
│   Models    │  │  (S3 + Vector Store) │
└─────────────┘  └──────────────────────┘
```

**Pros:**
- Minimal changes to existing code
- Adds RAG capabilities via Knowledge Base
- Lower operational complexity
- Faster to implement

**Cons:**
- Manual scaling and deployment
- No built-in session management
- Limited observability

**Implementation Steps:**
1. Create Knowledge Base with S3 data source
2. Add boto3 client for Knowledge Base retrieval
3. Integrate retrieval into agents (especially MatchmakingAgent)
4. Update agent prompts with retrieved context

---

### **Option 2: Hybrid - AgentCore Runtime + Knowledge Base**

**Replace:** FastAPI deployment with AgentCore Runtime
**Keep:** Strands Agents code (minimal changes)
**Add:** Knowledge Base, AgentCore services

```
┌─────────────┐
│   Express   │
│   Backend   │
└──────┬──────┘
       │ boto3 InvokeAgent API
       ▼
┌──────────────────────────────────────┐
│  Amazon Bedrock AgentCore Runtime    │
│  ┌────────────────────────────────┐  │
│  │  Your Strands Agents           │  │
│  │  (deployed as container/code)  │  │
│  │  - SourcingAgent               │  │
│  │  - MatchmakingAgent            │  │
│  │  - CollaboratorAgent           │  │
│  │  - DraftingAgent               │  │
│  │  - OrchestratorAgent           │  │
│  └────────────────────────────────┘  │
│                                       │
│  Built-in Services:                  │
│  - Session Isolation                 │
│  - Memory Management                 │
│  - Observability                     │
│  - Identity Management               │
└───────────────┬───────────────────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
┌─────────────┐  ┌──────────────────────┐
│   Bedrock   │  │  Knowledge Base      │
│   Models    │  │  (S3 + Vector Store) │
└─────────────┘  └──────────────────────┘
```

**Pros:**
- Enterprise-grade security and scaling
- Built-in session isolation (each user gets dedicated microVM)
- Integrated observability and tracing
- Consumption-based pricing
- Supports long-running agents (up to 8 hours)
- Built-in memory management

**Cons:**
- Requires deployment changes
- Learning curve for AgentCore
- Additional AWS service costs

**Implementation Steps:**
1. Add AgentCore decorators to Strands agents
2. Package agents as container or direct code
3. Deploy to AgentCore Runtime
4. Update Express to use boto3 `InvokeAgent` API
5. Create Knowledge Base and integrate

---

### **Option 3: Full AWS Native - Bedrock Agents + Knowledge Base**

**Replace:** Custom Strands agents with Amazon Bedrock Agents
**Use:** Native Bedrock multi-agent collaboration
**Add:** Knowledge Base integration

```
┌─────────────┐
│   Express   │
│   Backend   │
└──────┬──────┘
       │ boto3 InvokeAgent API
       ▼
┌──────────────────────────────────────┐
│  Amazon Bedrock Agents               │
│  ┌────────────────────────────────┐  │
│  │  Supervisor Agent              │  │
│  │  (orchestrates sub-agents)     │  │
│  │                                │  │
│  │  Sub-Agents:                   │  │
│  │  - Sourcing                    │  │
│  │  - Matchmaking                 │  │
│  │  - Collaborator                │  │
│  │  - Drafting                    │  │
│  └────────────────────────────────┘  │
│                                       │
│  Features:                            │
│  - Multi-agent collaboration         │
│  - Action Groups (Lambda functions)  │
│  - Knowledge Base integration        │
│  - Built-in orchestration            │
└───────────────┬───────────────────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
┌─────────────┐  ┌──────────────────────┐
│   Bedrock   │  │  Knowledge Base      │
│   Models    │  │  (S3 + Vector Store) │
└─────────────┘  └──────────────────────┘
```

**Pros:**
- Fully managed by AWS
- Native multi-agent collaboration
- No infrastructure management
- Built-in Knowledge Base integration
- Automatic orchestration

**Cons:**
- Complete rewrite of agent logic
- Less flexibility than custom code
- Vendor lock-in
- Higher learning curve

---

## Knowledge Base Integration Details

### What is Knowledge Bases for Amazon Bedrock?

A fully managed RAG (Retrieval Augmented Generation) service that:
1. Connects to data sources (S3, Confluence, SharePoint, etc.)
2. Automatically converts documents to embeddings
3. Stores embeddings in vector database
4. Provides retrieval APIs for agents

### S3 Data Source Setup

**Step 1: Prepare S3 Bucket**
```bash
# Create S3 bucket for grant data
aws s3 mb s3://fundingforge-knowledge-base

# Upload grant documents
aws s3 cp ./grant-policies/ s3://fundingforge-knowledge-base/policies/ --recursive
aws s3 cp ./grant-templates/ s3://fundingforge-knowledge-base/templates/ --recursive
aws s3 cp ./compliance-docs/ s3://fundingforge-knowledge-base/compliance/ --recursive
```

**Step 2: Create Knowledge Base**
```python
import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create knowledge base
kb_response = bedrock_agent.create_knowledge_base(
    name='FundingForgeKnowledgeBase',
    description='Grant policies, templates, and compliance documents',
    roleArn='arn:aws:iam::ACCOUNT:role/BedrockKnowledgeBaseRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': 'arn:aws:aoss:us-east-1:ACCOUNT:collection/...',
            'vectorIndexName': 'fundingforge-index',
            'fieldMapping': {
                'vectorField': 'embedding',
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }
)

knowledge_base_id = kb_response['knowledgeBase']['knowledgeBaseId']

# Create data source
ds_response = bedrock_agent.create_data_source(
    knowledgeBaseId=knowledge_base_id,
    name='S3GrantDocuments',
    dataSourceConfiguration={
        'type': 'S3',
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::fundingforge-knowledge-base',
            'inclusionPrefixes': ['policies/', 'templates/', 'compliance/']
        }
    }
)

# Start ingestion
bedrock_agent.start_ingestion_job(
    knowledgeBaseId=knowledge_base_id,
    dataSourceId=ds_response['dataSource']['dataSourceId']
)
```

**Step 3: Integrate with Agents**

```python
# In your MatchmakingAgent
from strands import Agent
from strands.models import BedrockModel
import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

async def run_matchmaking_agent(user_profile, sourced_data, match_criteria, eligibility):
    # Retrieve relevant compliance documents
    kb_response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId='YOUR_KB_ID',
        retrievalQuery={
            'text': f"FSU grant compliance requirements for {match_criteria}"
        },
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5
            }
        }
    )
    
    # Extract retrieved context
    retrieved_docs = [
        result['content']['text'] 
        for result in kb_response['retrievalResults']
    ]
    context = "\n\n".join(retrieved_docs)
    
    # Enhance agent prompt with retrieved context
    enhanced_prompt = f"""
    User Profile: {user_profile}
    Match Criteria: {match_criteria}
    
    Relevant Compliance Documents:
    {context}
    
    Analyze compliance based on the retrieved documents.
    """
    
    # Invoke agent with enhanced context
    response = await matchmaking_agent.run(enhanced_prompt)
    
    return response
```

---

## Recommended Implementation Plan

### **Phase 1: Add Knowledge Base (Week 1-2)**

**Goal:** Enhance existing agents with RAG capabilities

**Tasks:**
1. Create S3 bucket and upload grant documents
2. Set up Knowledge Base with S3 data source
3. Configure vector store (OpenSearch Serverless)
4. Start ingestion job
5. Add boto3 retrieval to MatchmakingAgent
6. Test retrieval quality

**Files to Modify:**
- `agent-service/agents/matchmaking.py` - Add KB retrieval
- `agent-service/requirements.txt` - Add boto3
- `agent-service/.env.example` - Add KB_ID

**Estimated Effort:** 2-3 days

---

### **Phase 2: Deploy to AgentCore Runtime (Week 3-4)**

**Goal:** Move from self-hosted FastAPI to managed AgentCore

**Tasks:**
1. Add AgentCore decorators to agents
2. Create Dockerfile for agent service
3. Deploy to AgentCore Runtime
4. Update Express to use InvokeAgent API
5. Test session isolation and memory
6. Set up observability

**Files to Modify:**
- `agent-service/agents/*.py` - Add AgentCore decorators
- `agent-service/Dockerfile` - Update for AgentCore
- `server/agent-client.ts` - Replace HTTP with boto3 SDK
- `package.json` - Add @aws-sdk/client-bedrock-agent-runtime

**Estimated Effort:** 5-7 days

---

### **Phase 3: Multi-Agent Orchestration (Week 5-6)**

**Goal:** Use native Bedrock multi-agent collaboration

**Tasks:**
1. Create supervisor agent in Bedrock
2. Convert specialized agents to Bedrock sub-agents
3. Configure action groups (Lambda functions)
4. Link Knowledge Base to agents
5. Test multi-agent collaboration
6. Migrate from custom orchestration

**Files to Modify:**
- Create new Lambda functions for action groups
- Update Express to invoke supervisor agent
- Remove custom orchestrator code

**Estimated Effort:** 7-10 days

---

## Cost Comparison

### Option 1: Current + Knowledge Base
- **FastAPI hosting:** $20-50/month (EC2 t3.medium)
- **Knowledge Base:** $0.10 per 1000 queries
- **Bedrock models:** ~$0.015 per proposal
- **Total (1000 proposals/month):** ~$85/month

### Option 2: AgentCore Runtime + Knowledge Base
- **AgentCore Runtime:** $0.0024 per minute (consumption-based)
- **Knowledge Base:** $0.10 per 1000 queries
- **Bedrock models:** ~$0.015 per proposal
- **Total (1000 proposals/month, 30s avg):** ~$135/month

### Option 3: Full Bedrock Agents
- **Bedrock Agents:** $0.002 per request
- **Knowledge Base:** $0.10 per 1000 queries
- **Bedrock models:** ~$0.015 per proposal
- **Total (1000 proposals/month):** ~$120/month

---

## Decision Matrix

| Criteria | Option 1 | Option 2 | Option 3 |
|----------|----------|----------|----------|
| **Implementation Time** | ⭐⭐⭐⭐⭐ (2-3 days) | ⭐⭐⭐ (1 week) | ⭐ (2-3 weeks) |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Scalability** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Operational Overhead** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cost (low volume)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Observability** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Security** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Recommendation

**For MVP/Current Stage:** **Option 1** (Current + Knowledge Base)
- Fastest to implement
- Adds significant value (RAG capabilities)
- Minimal risk
- Can migrate to Option 2 later

**For Production Scale:** **Option 2** (AgentCore Runtime + Knowledge Base)
- Best balance of flexibility and managed services
- Enterprise-grade security and scaling
- Keeps your custom agent logic
- Built-in observability

**For Full AWS Integration:** **Option 3** (Full Bedrock Agents)
- Only if you want complete AWS management
- Requires significant rewrite
- Less flexibility but fully managed

---

## Next Steps

1. **Immediate:** Implement Option 1 (add Knowledge Base)
2. **Short-term:** Evaluate AgentCore Runtime for production
3. **Long-term:** Consider full Bedrock Agents if scaling becomes complex

## Code Examples

### Knowledge Base Retrieval in MatchmakingAgent

```python
# agent-service/agents/matchmaking.py
import boto3
from strands import Agent
from strands.models import BedrockModel

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')

async def run_matchmaking_agent(
    user_profile: Dict[str, str],
    sourced_data: Dict[str, Any],
    match_criteria: str,
    eligibility: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Enhanced MatchmakingAgent with Knowledge Base retrieval
    """
    
    # Step 1: Retrieve relevant compliance documents
    yield {
        "agent": "matchmaking",
        "step": "Retrieving compliance documents from Knowledge Base...",
        "output": None,
        "done": False
    }
    
    try:
        kb_response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={
                'text': f"""
                Find compliance requirements for:
                - Grant: {match_criteria}
                - Eligibility: {eligibility}
                - Institution: FSU
                - Categories: RAMP, COI, IRB, Policy
                """
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 10,
                    'overrideSearchType': 'HYBRID'  # Combines semantic + keyword search
                }
            }
        )
        
        # Extract and format retrieved documents
        retrieved_context = []
        for result in kb_response['retrievalResults']:
            doc_text = result['content']['text']
            source = result['location']['s3Location']['uri']
            score = result['score']
            
            retrieved_context.append({
                'text': doc_text,
                'source': source,
                'relevance_score': score
            })
        
        context_text = "\n\n---\n\n".join([
            f"Source: {ctx['source']}\nRelevance: {ctx['relevance_score']:.2f}\n\n{ctx['text']}"
            for ctx in retrieved_context
        ])
        
    except Exception as e:
        logger.error(f"Knowledge Base retrieval failed: {e}")
        context_text = "No additional compliance documents retrieved."
    
    # Step 2: Analyze with enhanced context
    yield {
        "agent": "matchmaking",
        "step": "Analyzing match criteria with compliance context...",
        "output": None,
        "done": False
    }
    
    # Enhanced prompt with retrieved context
    enhanced_input = f"""
    Analyze this user's match for the grant and check compliance:

    User Profile:
    - Role: {user_profile.get('role')}
    - Year: {user_profile.get('year')}
    - Program: {user_profile.get('program')}
    - Experience: {sourced_data.get('experience', [])}
    - Expertise: {sourced_data.get('expertise', [])}

    Grant Requirements:
    - Match Criteria: {match_criteria}
    - Eligibility: {eligibility}

    Retrieved Compliance Documents:
    {context_text}

    Based on the retrieved documents, provide:
    1. Match score (0-100)
    2. Match justification
    3. Detailed compliance checklist with tasks, categories (RAMP/COI/IRB/Policy), and status (green/yellow/red)
    
    Be specific and cite the retrieved documents when making compliance recommendations.
    """
    
    # Invoke agent with enhanced context
    response = await matchmaking_agent.run(enhanced_input)
    
    # ... rest of the agent logic
```

### Express Backend with boto3 InvokeAgent (Option 2)

```typescript
// server/agent-client.ts
import { 
  BedrockAgentRuntimeClient, 
  InvokeAgentCommand 
} from "@aws-sdk/client-bedrock-agent-runtime";

const client = new BedrockAgentRuntimeClient({ 
  region: process.env.AWS_REGION || 'us-east-1' 
});

export async function* invokeAgentPipeline(
  payload: InvokePayload
): AsyncGenerator<JSONLine> {
  const agentId = process.env.BEDROCK_AGENT_ID!;
  const agentAliasId = process.env.BEDROCK_AGENT_ALIAS_ID!;
  
  const command = new InvokeAgentCommand({
    agentId,
    agentAliasId,
    sessionId: `session-${Date.now()}`,
    inputText: JSON.stringify(payload),
    enableTrace: true,  // Enable observability
    sessionState: {
      sessionAttributes: {
        grantId: payload.grantId.toString(),
        userRole: payload.userProfile.role
      }
    }
  });
  
  try {
    const response = await client.send(command);
    
    if (!response.completion) {
      throw new Error('No completion stream from agent');
    }
    
    // Stream responses
    for await (const event of response.completion) {
      if (event.chunk) {
        const chunk = JSON.parse(
          new TextDecoder().decode(event.chunk.bytes)
        );
        yield chunk as JSONLine;
      }
      
      if (event.trace) {
        // Log trace for observability
        console.log('Agent trace:', event.trace);
      }
    }
  } catch (error) {
    console.error('Error invoking agent:', error);
    throw error;
  }
}
```

---

## Conclusion

The current implementation is solid but can be significantly enhanced by:

1. **Adding Knowledge Base** for RAG capabilities (highest priority)
2. **Deploying to AgentCore Runtime** for production scalability
3. **Considering Bedrock Agents** for full AWS management (optional)

Start with Option 1 (Knowledge Base integration) as it provides immediate value with minimal changes.
