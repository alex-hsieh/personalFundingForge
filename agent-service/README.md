# FundingForge Agent Service

Python FastAPI microservice that orchestrates a multi-agent AI pipeline powered by AWS Strands Agents SDK and AWS Bedrock.

## Architecture

The agent service implements five specialized agents:
- **SourcingAgent** (Haiku): Extracts and structures user CV and profile data
- **MatchmakingAgent** (Haiku): Analyzes grant fit AND checks policy/compliance
- **CollaboratorAgent** (Haiku): Recommends relevant faculty collaborators
- **DraftingAgent** (Sonnet): Generates high-quality proposal narrative
- **OrchestratorAgent**: Coordinates execution of all agents in sequence

## Required Environment Variables

```bash
# AWS Configuration (REQUIRED)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock Model Configuration (OPTIONAL - defaults provided)
BEDROCK_MODEL_DRAFTING=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_FAST=anthropic.claude-haiku-4-5-20251001-v1:0

# Service Configuration (OPTIONAL)
PORT=8001
```

## Required IAM Permissions

Your AWS credentials must have the following permissions:

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
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6"
      ]
    }
  ]
}
```

## Local Development Setup

### 1. Create Virtual Environment

```bash
cd agent-service
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your AWS credentials
# IMPORTANT: Never commit .env to version control
```

### 4. Run the Service

```bash
# Development mode with auto-reload
uvicorn main:app --port 8001 --reload

# Production mode
python main.py
```

### 5. Access API Documentation

Once running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- Health Check: http://localhost:8001/health

## Running Jupyter Notebooks

The `notebooks/` directory contains isolated testing notebooks for each agent:

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook notebooks/

# Open and run notebooks in order:
# 01_sourcing_agent.ipynb
# 02_matchmaking_agent.ipynb
# 03_collaborator_agent.ipynb
# 04_drafting_agent.ipynb
# 05_orchestrator_agent.ipynb
# 06_full_pipeline.ipynb
```

## Docker Deployment

### Build Image

```bash
docker build -t fundingforge-agent-service .
```

### Run Container

```bash
docker run -d \
  -p 8001:8001 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  --name fundingforge-agents \
  fundingforge-agent-service
```

### Check Health

```bash
curl http://localhost:8001/health
```

## API Endpoints

### POST /invoke

Invokes the multi-agent pipeline for grant proposal generation.

**Request Body:**
```json
{
  "grantId": 1,
  "grantName": "NSF GRFP",
  "matchCriteria": "PhD students in STEM fields...",
  "eligibility": "Must be US citizen or permanent resident...",
  "userProfile": {
    "role": "PhD Student",
    "year": "2nd Year",
    "program": "Computer Science"
  },
  "facultyList": [
    {
      "name": "Dr. Jane Smith",
      "department": "Computer Science",
      "expertise": "Machine Learning, AI",
      "imageUrl": "https://example.com/image.jpg",
      "bio": "Professor of Computer Science..."
    }
  ]
}
```

**Response:** Streaming newline-delimited JSON (application/x-ndjson)

Each line is a JSON object with format:
```json
{
  "agent": "sourcing|matchmaking|collaborator|drafting|orchestrator",
  "step": "Human-readable progress message",
  "output": null,
  "done": false
}
```

Final line includes complete result:
```json
{
  "agent": "orchestrator",
  "step": "Complete",
  "output": {
    "proposalDraft": "...",
    "collaborators": [...],
    "matchScore": 85,
    "matchJustification": "...",
    "complianceChecklist": [...]
  },
  "done": true
}
```

## Cost Considerations

### Pricing (as of 2024)
- **Claude Haiku**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- **Claude Sonnet**: ~$3 per 1M input tokens, ~$15 per 1M output tokens

### Typical Pipeline Cost
- SourcingAgent: 200 input + 300 output tokens (~$0.0004)
- MatchmakingAgent: 400 input + 500 output tokens (~$0.0007)
- CollaboratorAgent: 300 input + 200 output tokens (~$0.0003)
- DraftingAgent: 600 input + 400 output tokens (~$0.0078)

**Estimated cost per proposal: ~$0.015**

### Monitoring Recommendations

1. **CloudWatch Metrics**: Track Bedrock API calls and latency
2. **Cost Alerts**: Set up billing alerts for unexpected usage
3. **Token Tracking**: Log token usage per agent for optimization
4. **Error Monitoring**: Alert on high error rates or throttling

## Troubleshooting

### "Missing environment variables" error
- Ensure all required AWS credentials are set in `.env`
- Check that `.env` file is in the same directory as `main.py`
- Verify environment variables are exported if not using `.env`

### "AccessDeniedException" from Bedrock
- Verify IAM permissions include `bedrock:InvokeModel`
- Check that model IDs are correct and available in your region
- Ensure AWS credentials are valid and not expired

### "ThrottlingException" from Bedrock
- Bedrock has rate limits per model
- Implement exponential backoff (already included via tenacity)
- Consider requesting quota increases for production

### Agent service unreachable from Express backend
- Verify agent service is running on port 8001
- Check firewall rules allow connections
- Ensure `AGENT_SERVICE_URL` in Express backend points to correct URL
- Test health endpoint: `curl http://localhost:8001/health`

## Development Workflow

1. **Prototype in Notebooks**: Test individual agents in isolation
2. **Implement Agents**: Create agent files in `agents/` directory
3. **Wire to Orchestrator**: Connect agents in `agents/orchestrator.py`
4. **Update main.py**: Replace placeholder with orchestrator
5. **Test Locally**: Run service and test with sample requests
6. **Deploy**: Build Docker image and deploy to production

## Security Best Practices

- ✅ Never commit AWS credentials to version control
- ✅ Use IAM roles in production (avoid access keys)
- ✅ Rotate credentials regularly
- ✅ Implement least-privilege IAM policies
- ✅ Validate all inputs before passing to agents
- ✅ Sanitize all outputs before streaming
- ✅ Use HTTPS in production
- ✅ Implement rate limiting
- ✅ Monitor for unusual activity

## Support

For issues or questions:
1. Check this README for troubleshooting steps
2. Review agent implementation in `agents/` directory
3. Test individual agents using Jupyter notebooks
4. Check logs for detailed error messages
