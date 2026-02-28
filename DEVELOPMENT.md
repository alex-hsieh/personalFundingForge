# Development Guide

This guide provides detailed information for developers working on FundingForge.

## Architecture Overview

### System Flow

```
User Request → Frontend (React)
    ↓
Express Backend (/api/forge/:grantId)
    ↓
Fetch Grant & Faculty from PostgreSQL
    ↓
Build InvokePayload
    ↓
AWS AgentCore (localhost:8000)
    ↓
Python Agent Service (localhost:8001)
    ↓
OrchestratorAgent
    ↓
SourcingAgent → MatchmakingAgent → CollaboratorAgent → DraftingAgent
    ↓
AWS Bedrock (Claude Haiku & Sonnet)
    ↓
Stream JSON_Line responses back through chain
    ↓
Transform to SSE format
    ↓
Frontend displays real-time updates
```

### Data Flow

1. **User Input**: Role, Year, Program, Grant Selection
2. **Database Query**: Fetch grant details and faculty list
3. **Agent Pipeline**:
   - SourcingAgent: Extract user data → structured output
   - MatchmakingAgent: Analyze fit + compliance → score + checklist
   - CollaboratorAgent: Match faculty → top 3 recommendations
   - DraftingAgent: Generate proposal → 300-500 word draft
4. **Result**: Complete proposal package with all components

## Local Development Setup

### Terminal Setup (Recommended)

**Terminal 1 - PostgreSQL:**
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```

**Terminal 2 - Agent Service:**
```bash
cd agent-service
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 3 - Express Backend:**
```bash
npm run dev
```

**Terminal 4 - Development Tasks:**
```bash
# Run tests, check types, etc.
npm run check
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Agent Development

### Agent Implementation Checklist

When implementing a new agent:

- [ ] Create agent file in `agent-service/agents/`
- [ ] Import `Agent` and `BedrockModel` from strands
- [ ] Choose appropriate model (Haiku for speed, Sonnet for quality)
- [ ] Write comprehensive system prompt
- [ ] Implement async run function
- [ ] Add JSON_Line streaming with progress updates
- [ ] Create Jupyter notebook for isolated testing
- [ ] Write unit tests
- [ ] Write property-based tests
- [ ] Update orchestrator to include agent
- [ ] Document in README

### System Prompt Best Practices

1. **Be Specific**: Clearly define the agent's role and responsibilities
2. **Provide Context**: Explain what data the agent receives
3. **Define Output Format**: Specify exact JSON structure expected
4. **Include Examples**: Show sample inputs and outputs
5. **Set Constraints**: Word limits, required fields, validation rules

**Example:**
```python
SYSTEM_PROMPT = """
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
"""
```

### Testing Agents in Jupyter

1. Start Jupyter: `jupyter notebook agent-service/notebooks/`
2. Open relevant notebook (e.g., `01_sourcing_agent.ipynb`)
3. Run cells to test agent in isolation
4. Iterate on system prompt and logic
5. Export working code to agent file

### Debugging Agent Issues

**Check Agent Service Logs:**
```bash
# In agent service terminal
# Logs show each agent invocation and errors
```

**Test Individual Agent:**
```python
# In Python REPL or notebook
from agents.sourcing import sourcing_agent

result = await sourcing_agent.run({
    "userProfile": {
        "role": "PhD Student",
        "year": "2nd Year",
        "program": "Computer Science"
    }
})
print(result)
```

**Verify JSON_Line Format:**
```bash
# Test /invoke endpoint directly
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

## Express Backend Development

### Adding New Endpoints

1. **Define Schema** in `shared/routes.ts`:
```typescript
export const api = {
  newEndpoint: {
    method: 'GET' as const,
    path: '/api/new-endpoint' as const,
    responses: {
      200: z.object({ data: z.string() })
    }
  }
};
```

2. **Implement Route** in `server/routes.ts`:
```typescript
app.get('/api/new-endpoint', async (req, res) => {
  // Implementation
  res.json({ data: "result" });
});
```

3. **Add Storage Method** if needed in `server/storage.ts`:
```typescript
export async function getNewData() {
  return db.select().from(newTable);
}
```

4. **Create Frontend Hook** in `client/src/hooks/`:
```typescript
export function useNewData() {
  return useQuery({
    queryKey: ['new-data'],
    queryFn: async () => {
      const res = await fetch('/api/new-endpoint');
      return res.json();
    }
  });
}
```

### SSE Streaming Pattern

```typescript
app.get('/api/stream-endpoint', async (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  try {
    // Stream data
    for await (const chunk of dataSource) {
      res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    }
    res.end();
  } catch (error) {
    res.write(`data: ${JSON.stringify({ error: true })}\n\n`);
    res.end();
  }
});
```

## Frontend Development

### Component Structure

```typescript
// client/src/components/NewComponent.tsx
import { useState } from 'react';
import { Card } from './ui/card';

interface NewComponentProps {
  data: string;
  onAction: () => void;
}

export function NewComponent({ data, onAction }: NewComponentProps) {
  const [state, setState] = useState<string>('');
  
  return (
    <Card>
      {/* Component content */}
    </Card>
  );
}
```

### Using SSE Streams

```typescript
// client/src/hooks/use-stream.ts
export function useStream(url: string) {
  const [messages, setMessages] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  
  useEffect(() => {
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data.step]);
      if (data.done) {
        setDone(true);
        eventSource.close();
      }
    };
    
    return () => eventSource.close();
  }, [url]);
  
  return { messages, done };
}
```

## Database Development

### Schema Changes

1. Update `shared/schema.ts`:
```typescript
export const newTable = pgTable('new_table', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  createdAt: timestamp('created_at').defaultNow()
});
```

2. Push changes:
```bash
npm run db:push
```

3. Update storage layer:
```typescript
// server/storage.ts
export async function getNewTableData() {
  return db.select().from(newTable);
}
```

### Querying Data

```typescript
// Simple select
const grants = await db.select().from(grants);

// With conditions
const grant = await db
  .select()
  .from(grants)
  .where(eq(grants.id, grantId))
  .limit(1);

// With joins
const result = await db
  .select()
  .from(grants)
  .leftJoin(faculty, eq(grants.facultyId, faculty.id));
```

## Testing

### Running Tests

```bash
# Type checking
npm run check

# E2E tests
npm test

# Watch mode
npm test -- --ui

# Specific test file
npm test tests/example.spec.ts
```

### Writing Tests

```typescript
// tests/new-feature.spec.ts
import { test, expect } from '@playwright/test';

test('new feature works', async ({ page }) => {
  await page.goto('/');
  await page.click('button[data-testid="new-feature"]');
  await expect(page.locator('.result')).toBeVisible();
});
```

## Debugging

### Backend Debugging

```typescript
// Add console.log statements
console.log('Debug:', { variable, data });

// Use debugger
debugger;

// Check environment
console.log('Env:', process.env.AGENT_SERVICE_URL);
```

### Agent Service Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing: {data}")

# Use breakpoint
breakpoint()

# Check environment
import os
print(f"AWS Region: {os.getenv('AWS_REGION')}")
```

### Frontend Debugging

```typescript
// React DevTools
// Browser console
console.log('State:', state);

// Network tab for API calls
// React Query DevTools
```

## Performance Optimization

### Agent Service

- Use Haiku for fast operations (sourcing, matching, collaborator)
- Reserve Sonnet for quality-critical operations (drafting)
- Implement request batching where possible
- Monitor token usage and optimize prompts
- Consider prompt caching for repeated patterns

### Express Backend

- Cache grant and faculty queries
- Use connection pooling for database
- Implement rate limiting
- Monitor memory usage during streaming

### Frontend

- Lazy load components
- Memoize expensive computations
- Optimize re-renders with React.memo
- Use virtual scrolling for long lists

## Common Issues

### "Agent service unreachable"

- Check agent service is running: `curl http://localhost:8001/health`
- Verify `AGENT_SERVICE_URL` in `.env`
- Check firewall rules

### "AccessDeniedException" from Bedrock

- Verify IAM permissions include `bedrock:InvokeModel`
- Check AWS credentials are set correctly
- Ensure model IDs are correct

### "Database connection failed"

- Verify PostgreSQL is running
- Check `DATABASE_URL` format
- Ensure database exists

### Frontend not updating

- Check browser console for errors
- Verify SSE connection in Network tab
- Check Express backend logs

## Best Practices

### Security

- Never commit `.env` files
- Use environment variables for secrets
- Validate all user inputs
- Sanitize all outputs
- Implement rate limiting
- Use HTTPS in production

### Code Quality

- Write tests for new features
- Keep functions small and focused
- Use meaningful names
- Add comments for complex logic
- Follow existing patterns

### Git Workflow

- Create feature branches
- Write descriptive commit messages
- Keep commits atomic
- Rebase before merging
- Delete merged branches

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Express.js Guide](https://expressjs.com/)
- [React Documentation](https://react.dev/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Drizzle ORM](https://orm.drizzle.team/)

## Getting Help

1. Check this guide
2. Review existing code
3. Check logs for errors
4. Open an issue
5. Ask in pull request

Happy coding! 🚀
