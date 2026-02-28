# Migration Notes

## AWS AgentCore Clarification (Resolved)

### Problem
The initial setup attempted to use `@aws-sdk/client-agentcore`, which doesn't exist as an npm package.

### Root Cause
**Misunderstanding of AWS Bedrock AgentCore**: AgentCore is a managed runtime service for deploying AI agents to AWS infrastructure, not a client SDK for making API calls. It's similar to AWS Fargate - you deploy containers to it, but you don't need an SDK to communicate with your own services.

### Solution
**Removed the non-existent dependency** and clarified the architecture uses direct HTTP calls from Express to the FastAPI agent service.

### Correct Architecture

```
Frontend → Express Backend → Python Agent Service (FastAPI) → AWS Bedrock
```

**Not:**
```
Frontend → Express Backend → AgentCore SDK → Agent Service
```

### What is AWS Bedrock AgentCore?

AgentCore is a **deployment platform** for AI agents, providing:
- Managed runtime environment
- Automatic scaling
- Built-in memory and identity management
- Gateway integrations

It's used to **deploy** agents to AWS infrastructure, not to communicate between services in your application.

### Our Implementation

We use **direct HTTP calls** from Express to the FastAPI agent service:
- Simple and straightforward
- No unnecessary abstraction layer
- Works perfectly for local development and production
- Agent service can be deployed anywhere (local, Docker, AWS, etc.)

### Changes Made

1. **package.json** - Removed non-existent `@aws-sdk/client-agentcore`
2. **server/agentcore-client.ts** - Renamed to reflect direct HTTP communication
3. **.env.example** - Removed AGENTCORE_ENDPOINT (not needed)
4. **Documentation** - Updated to reflect correct architecture

### Testing

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Verify no errors
npm run check
```

### No Functional Impact

This clarification has **no impact on functionality**:
- ✅ Agent service works the same
- ✅ SSE streaming works
- ✅ All features intact
- ✅ Simpler, more maintainable architecture

---

**Status**: ✅ Resolved
**Date**: 2024
**Impact**: Build errors resolved, architecture clarified

