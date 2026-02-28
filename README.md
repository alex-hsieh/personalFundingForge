# FundingForge

AI-powered grant proposal generation platform with multi-agent orchestration.

## Architecture

FundingForge uses a multi-agent AI pipeline powered by AWS Bedrock to generate personalized grant proposals:

```
Frontend (React) → Express Backend → Python Agent Service (FastAPI) → AWS Bedrock
```

### Components

1. **Frontend**: React + TypeScript with Wouter routing and Tailwind CSS
2. **Express Backend**: REST API with SSE streaming for real-time updates
3. **Python Agent Service**: FastAPI microservice orchestrating 5 specialized agents
4. **AWS Bedrock**: Foundation models (Claude Haiku & Sonnet)

### Five Specialized Agents

- **SourcingAgent** (Haiku): Extracts user CV and profile data
- **MatchmakingAgent** (Haiku): Analyzes grant fit + policy compliance
- **CollaboratorAgent** (Haiku): Recommends faculty collaborators
- **DraftingAgent** (Sonnet): Generates high-quality proposal narrative
- **OrchestratorAgent**: Coordinates all agents in sequence

## Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.11+
- **PostgreSQL** 15+
- **AWS Account** with Bedrock access
- **AWS Credentials** with `bedrock:InvokeModel` permissions

## Quick Start

### 1. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd fundingforge

# Install Node.js dependencies
npm install

# Install Python dependencies
cd agent-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 2. Configure Environment

```bash
# Copy environment templates
cp .env.example .env
cp agent-service/.env.example agent-service/.env

# Edit .env files with your credentials
# IMPORTANT: Set AWS credentials and DATABASE_URL
```

### 3. Start PostgreSQL

```bash
# Using Docker
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=fundingforge \
  --name fundingforge-db \
  postgres:15

# Or use your existing PostgreSQL instance
```

### 4. Initialize Database

```bash
npm run db:push
```

### 5. Start Services

**Terminal 1 - Agent Service:**
```bash
cd agent-service
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
# Runs on http://localhost:8001
```

**Terminal 2 - Express Backend:**
```bash
npm run dev
# Runs on http://localhost:5000
```

### 6. Access Application

Open http://localhost:5000 in your browser.

## Development Workflow

### Project Structure

```
fundingforge/
├── agent-service/          # Python FastAPI agent service
│   ├── agents/            # Agent implementations
│   ├── notebooks/         # Jupyter notebooks for testing
│   ├── main.py           # FastAPI app
│   ├── models.py         # Pydantic models
│   └── requirements.txt
├── client/                # React frontend
│   └── src/
│       ├── components/   # UI components
│       ├── pages/        # Page components
│       └── hooks/        # Custom hooks
├── server/               # Express backend
│   ├── agentcore-client.ts  # AgentCore integration
│   ├── routes.ts         # API routes
│   ├── storage.ts        # Database layer
│   └── index.ts          # Server entry point
├── shared/               # Shared TypeScript types
│   ├── schema.ts         # Database schema
│   └── routes.ts         # API contracts
└── tests/                # E2E tests
```

### Running Tests

```bash
# TypeScript type checking
npm run check

# E2E tests
npm test

# Python tests (when implemented)
cd agent-service
pytest
```

### Database Migrations

```bash
# Push schema changes
npm run db:push

# Generate migrations (if using drizzle-kit migrate)
npx drizzle-kit generate
```

## API Endpoints

### REST Endpoints

- `GET /api/grants` - List all grants
- `GET /api/faculty` - List all faculty members

### Streaming Endpoints

- `GET /api/forge/:grantId?role=X&year=Y&program=Z` - Generate proposal (SSE stream)

### Agent Service Endpoints

- `GET /health` - Health check
- `POST /invoke` - Invoke multi-agent pipeline (streaming JSON)

## Environment Variables

### Express Backend (.env)

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/fundingforge
AGENT_SERVICE_URL=http://localhost:8001
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
SESSION_SECRET=your_session_secret
```

### Agent Service (agent-service/.env)

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_DRAFTING=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_FAST=anthropic.claude-haiku-4-5-20251001-v1:0
PORT=8001
```

## Deployment

### Docker Deployment

**Build Agent Service:**
```bash
cd agent-service
docker build -t fundingforge-agent-service .
docker run -d \
  -p 8001:8001 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  fundingforge-agent-service
```

**Build Express Backend:**
```bash
npm run build
npm start
```

### Production Considerations

1. **Use IAM Roles**: Replace AWS access keys with IAM roles
2. **Enable HTTPS**: Use reverse proxy (nginx, Caddy)
3. **Database**: Use managed PostgreSQL (RDS, Supabase)
4. **Monitoring**: Set up CloudWatch for Bedrock API calls
5. **Rate Limiting**: Implement rate limiting on /api/forge
6. **Caching**: Cache grant and faculty queries
7. **Scaling**: Horizontally scale agent service

## Cost Estimation

### AWS Bedrock Pricing (as of 2024)

- **Claude Haiku**: $0.25 per 1M input tokens, $1.25 per 1M output tokens
- **Claude Sonnet**: $3 per 1M input tokens, $15 per 1M output tokens

### Typical Pipeline Cost

Per proposal generation:
- SourcingAgent: ~$0.0004
- MatchmakingAgent: ~$0.0007
- CollaboratorAgent: ~$0.0003
- DraftingAgent: ~$0.0078

**Total: ~$0.015 per proposal**

## Troubleshooting

### Agent Service Won't Start

- Check AWS credentials are set in `.env`
- Verify Python dependencies installed: `pip install -r requirements.txt`
- Check port 8001 is not in use

### Express Backend Can't Connect to Agent Service

- Verify agent service is running: `curl http://localhost:8001/health`
- Check `AGENT_SERVICE_URL` in Express `.env`
- Review firewall rules

### Database Connection Errors

- Verify PostgreSQL is running
- Check `DATABASE_URL` format: `postgresql://user:password@host:port/database`
- Ensure database exists: `createdb fundingforge`

### AWS Bedrock Errors

- **AccessDeniedException**: Check IAM permissions include `bedrock:InvokeModel`
- **ThrottlingException**: Rate limits exceeded, implement backoff
- **ValidationException**: Verify model IDs are correct

### Frontend Not Loading

- Check Express backend is running on port 5000
- Clear browser cache
- Check browser console for errors

## Security Best Practices

- ✅ Never commit `.env` files to version control
- ✅ Use IAM roles in production (avoid access keys)
- ✅ Rotate credentials regularly
- ✅ Implement rate limiting on public endpoints
- ✅ Validate all user inputs
- ✅ Use HTTPS in production
- ✅ Keep dependencies updated
- ✅ Monitor for unusual activity

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests: `npm run check`
4. Submit pull request

## License

MIT

## Support

For issues or questions:
1. Check this README for troubleshooting
2. Review agent service README: `agent-service/README.md`
3. Check logs for detailed error messages
4. Open an issue on GitHub
