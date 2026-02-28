import os
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from models import InvokeRequest

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fundingforge.agents")

# Validate required environment variables
required_vars = ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    logger.error(f"Missing required environment variables: {missing}")
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

# Create FastAPI app
app = FastAPI(title="FundingForge Agent Service", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fundingforge-agent-service"}


@app.post("/invoke")
async def invoke_pipeline(request: InvokeRequest):
    """
    Invoke the multi-agent pipeline for grant proposal generation.
    
    Streams JSON_Line outputs as newline-delimited JSON.
    """
    # TODO: Wire up OrchestratorAgent
    async def generate():
        # Placeholder - will be replaced with orchestrator_agent.run(request)
        import json
        yield json.dumps({
            "agent": "system",
            "step": "Agent service initialized",
            "output": None,
            "done": False
        }) + "\n"
        
        yield json.dumps({
            "agent": "system",
            "step": "Complete",
            "output": {
                "proposalDraft": "Placeholder proposal",
                "collaborators": [],
                "matchScore": 0,
                "matchJustification": "Placeholder",
                "complianceChecklist": []
            },
            "done": True
        }) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
