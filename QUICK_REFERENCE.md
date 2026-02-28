# Quick Reference Card

## 🚀 Start Development

```bash
# Terminal 1: Agent Service
cd agent-service
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py

# Terminal 2: Express Backend
npm run dev

# Terminal 3: PostgreSQL (if not using Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```

## 📡 Service URLs

- **Frontend**: http://localhost:5000
- **Express API**: http://localhost:5000/api
- **Agent Service**: http://localhost:8001
- **Agent Service Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🔑 Environment Variables

### Express Backend (.env)
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fundingforge
AGENT_SERVICE_URL=http://localhost:8001
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Agent Service (agent-service/.env)
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_DRAFTING=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_FAST=anthropic.claude-haiku-4-5-20251001-v1:0
```

## 📦 Common Commands

### Node.js
```bash
npm install              # Install dependencies
npm run dev             # Start development server
npm run build           # Build for production
npm run check           # TypeScript type checking
npm test                # Run E2E tests
npm run db:push         # Push database schema
```

### Python
```bash
pip install -r requirements.txt    # Install dependencies
python main.py                     # Start agent service
pytest                             # Run tests (when implemented)
jupyter notebook notebooks/        # Start Jupyter
```

### Docker
```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f            # View logs
docker-compose ps                 # List services
```

## 🏗️ Project Structure

```
fundingforge/
├── agent-service/        # Python FastAPI agent service
│   ├── agents/          # Agent implementations
│   ├── notebooks/       # Jupyter notebooks
│   ├── main.py         # FastAPI app
│   └── models.py       # Pydantic models
├── client/             # React frontend
│   └── src/
├── server/             # Express backend
│   ├── agentcore-client.ts
│   ├── routes.ts
│   └── storage.ts
└── shared/             # Shared types
    ├── schema.ts       # Database schema
    └── routes.ts       # API contracts
```

## 🤖 Agent Pipeline

```
SourcingAgent (Haiku)
    ↓ Extract user data
MatchmakingAgent (Haiku)
    ↓ Analyze fit + compliance
CollaboratorAgent (Haiku)
    ↓ Find faculty matches
DraftingAgent (Sonnet)
    ↓ Generate proposal
OrchestratorAgent
    ↓ Coordinate all agents
Result: Complete proposal package
```

## 🔍 Debugging

### Check Service Health
```bash
curl http://localhost:8001/health
curl http://localhost:5000/api/grants
```

### View Logs
```bash
# Agent service logs (in terminal)
# Express backend logs (in terminal)
# Docker logs
docker-compose logs -f agent-service
```

### Test Agent Endpoint
```bash
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "grantId": 1,
    "grantName": "Test Grant",
    "matchCriteria": "Test criteria",
    "eligibility": "Test eligibility",
    "userProfile": {
      "role": "PhD Student",
      "year": "2nd Year",
      "program": "Computer Science"
    },
    "facultyList": []
  }'
```

## 📝 API Endpoints

### REST
- `GET /api/grants` - List grants
- `GET /api/faculty` - List faculty

### SSE Streaming
- `GET /api/forge/:grantId?role=X&year=Y&program=Z` - Generate proposal

### Agent Service
- `GET /health` - Health check
- `POST /invoke` - Invoke pipeline

## 🧪 Testing

```bash
# Type checking
npm run check

# E2E tests
npm test

# Property-based tests (when implemented)
npm test -- --grep "Property"
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Agent service won't start | Check AWS credentials in `.env` |
| Can't connect to database | Verify PostgreSQL is running |
| Import errors in Python | Activate venv: `source venv/bin/activate` |
| Frontend not loading | Check Express backend is running |
| AWS AccessDenied | Verify IAM permissions for Bedrock |

## 📚 Documentation

- **README.md** - Project overview
- **CONTRIBUTING.md** - How to contribute
- **DEVELOPMENT.md** - Development guide
- **agent-service/README.md** - Agent service docs
- **PROJECT_SETUP_SUMMARY.md** - Setup summary

## 💰 Cost Estimate

Per proposal generation: ~$0.015
- SourcingAgent: ~$0.0004
- MatchmakingAgent: ~$0.0007
- CollaboratorAgent: ~$0.0003
- DraftingAgent: ~$0.0078

## 🔐 Security Checklist

- [ ] AWS credentials in `.env` (not committed)
- [ ] `.env` files in `.gitignore`
- [ ] IAM permissions configured
- [ ] Rate limiting enabled (production)
- [ ] HTTPS enabled (production)
- [ ] Input validation implemented
- [ ] Output sanitization implemented

## 🎯 Implementation Order

1. ✅ Setup infrastructure (DONE)
2. Implement SourcingAgent
3. Implement MatchmakingAgent
4. Implement CollaboratorAgent
5. Implement DraftingAgent
6. Implement OrchestratorAgent
7. Wire to FastAPI endpoint
8. Update Express backend
9. Create Jupyter notebooks
10. Add comprehensive tests

## 🆘 Getting Help

1. Check documentation
2. Review logs
3. Test individual components
4. Open an issue
5. Ask in pull request

---

**Keep this file handy for quick reference during development!**
