# FundingForge Agent Service

Python FastAPI microservice that orchestrates a multi-agent AI pipeline for grant proposal generation using AWS Strands Agents SDK and AWS Bedrock.

## Architecture

The service implements five specialized agents:

1. **SourcingAgent** (Haiku) - Extracts and structures user CV and profile data
2. **MatchmakingAgent** (Haiku) - Analyzes grant fit AND checks policy/compliance
3. **CollaboratorAgent** (Haiku) - Finds and ranks relevant faculty collaborators
4. **DraftingAgent** (Sonnet) - Generates high-quality proposal narrative
5. **OrchestratorAgent** - Coordinates execution of all specialized agents

## Requirements

- Python 3.11 or later
- AWS credentials with Bedrock access
- Required IAM permissions:
  - `bedrock:InvokeModel` for Claude Haiku and Sonnet models
  - `bedrock:InvokeModelWithResponseStream` for streaming responses

## Environment Variables

Create a `.env` file in the `agent-service/` directory:

```bash
# Required
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Optional (with defaults)
BEDROCK_MODEL_DRAFTING=anthropic.claude-sonnet-4-6
BEDROCK_MODEL_FAST=anthropic.claude-haiku-4-5-20251001-v1:0
PORT=8001
```

## Installation

```bash
cd agent-service
pip install -r requirements.txt
```

## Running Locally

```bash
# From agent-service directory
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The service will be available at `http://localhost:8001`

## API Endpoints

### POST /invoke

Invokes the multi-agent pipeline for grant proposal generation.

**Request Body:**
```json
{
  "grantId": 1,
  "grantName": "NSF GRFP",
  "matchCriteria": "STEM, Social Science, Research",
  "eligibility": "Year 1-2 PhD",
  "userProfile": {
    "role": "PhD Student",
    "year": "Year 1",
    "program": "Computer Science"
  },
  "facultyList": [
    {
      "name": "Dr. Sarah Chen",
      "department": "Computer Science",
      "expertise": "AI, Machine Learning",
      "imageUrl": "https://example.com/image.jpg",
      "bio": "Dr. Chen focuses on neural architecture search..."
    }
  ]
}
```

**Response:** Streaming newline-delimited JSON (application/x-ndjson)

Each line is a JSON object with the format:
```json
{
  "agent": "sourcing|matchmaking|collaborator|drafting|orchestrator",
  "step": "Human-readable progress message",
  "output": null,
  "done": false
}
```

Final message (done=true):
```json
{
  "agent": "orchestrator",
  "step": "Complete",
  "output": {
    "proposalDraft": "...",
    "collaborators": [...],
    "matchScore": 75,
    "matchJustification": "...",
    "complianceChecklist": [...]
  },
  "done": true
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "fundingforge-agent-service"
}
```

## Docker

Build and run using Docker:

```bash
# Build image
docker build -t fundingforge-agent-service .

# Run container
docker run -p 8001:8001 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  fundingforge-agent-service
```

## Testing with Jupyter Notebooks

The `notebooks/` directory contains interactive notebooks for testing each agent:

- `01_sourcing_agent.ipynb` - Test SourcingAgent
- `02_matchmaking_agent.ipynb` - Test MatchmakingAgent
- `03_collaborator_agent.ipynb` - Test CollaboratorAgent
- `04_drafting_agent.ipynb` - Test DraftingAgent
- `05_orchestrator_agent.ipynb` - Test OrchestratorAgent
- `06_full_pipeline.ipynb` - Test complete pipeline

## Cost Considerations

AWS Bedrock pricing (as of 2024):
- Claude Haiku: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- Claude Sonnet: ~$3 per 1M input tokens, ~$15 per 1M output tokens

Estimated cost per proposal generation: $0.05 - $0.15

## Monitoring

Monitor agent performance:
- Check CloudWatch logs for Bedrock API calls
- Track token usage in CloudWatch metrics
- Monitor response times and error rates

## Troubleshooting

**Issue: "Missing environment variables"**
- Ensure all required environment variables are set
- Check `.env` file is in the correct directory

**Issue: "Bedrock model not found"**
- Verify model IDs are correct
- Ensure your AWS account has access to Claude models in Bedrock
- Check AWS region supports the models

**Issue: "Agent service unreachable"**
- Verify service is running on port 8001
- Check firewall settings
- Ensure AGENT_SERVICE_URL is set correctly in Express backend

## Development

The agent implementations use the Strands Agents SDK:

```python
from strands import Agent
from strands.models import BedrockModel

# Create model
model = BedrockModel(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")

# Create agent
agent = Agent(model=model, system_prompt="Your system prompt here")

# Run agent
response = await agent.run("User input")
```

## License

MIT
