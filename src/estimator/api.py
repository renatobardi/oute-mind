#!/usr/bin/env python
"""FastAPI wrapper for CrewAI software estimator"""

import os
from dotenv import load_dotenv

# Load environment variables FIRST (before any other imports)
# Try .env.production first, then .env
_env_path = "/app/.env.production" if os.path.exists("/app/.env.production") else ".env"
load_dotenv(_env_path, override=True)

# Explicitly ensure OPENAI_API_KEY is set from file
# This is required for CrewAI/LiteLLM to initialize (even though we use Google Gemini)
if "OPENAI_API_KEY" not in os.environ or not os.environ.get("OPENAI_API_KEY"):
    try:
        with open(_env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    key_value = line.strip().split('=', 1)[1] if '=' in line else None
                    if key_value:
                        os.environ['OPENAI_API_KEY'] = key_value
                        break
    except Exception as e:
        print(f"Warning: Could not read OPENAI_API_KEY from {_env_path}: {e}")

# Now import the crew after env vars are loaded
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from estimator.crew import SoftwareProjectEstimatorWithRagCrew

# Create FastAPI app
app = FastAPI(
    title="Software Estimator API",
    description="CrewAI-powered software project estimation API",
    version="1.0.0"
)

# Models
class EstimationRequest(BaseModel):
    estimation_id: str
    project_details: str | None = None

class EstimationResponse(BaseModel):
    estimation_id: str
    result: str
    status: str = "success"

# Lazy crew initialization
_crew_instance = None

def get_crew():
    """Lazy load the crew instance"""
    global _crew_instance
    if _crew_instance is None:
        try:
            _crew_instance = SoftwareProjectEstimatorWithRagCrew()
        except Exception as e:
            print(f"Warning: Failed to initialize crew: {e}")
            raise
    return _crew_instance

@app.get("/health")
async def health_check():
    """Health check endpoint - lightweight check that doesn't require crew"""
    return {
        "status": "healthy",
        "service": "software-estimator"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    try:
        crew = get_crew()
        crew_status = "ready"
    except:
        crew_status = "initializing"

    return {
        "status": "running",
        "service": "software-estimator",
        "version": "1.0.0",
        "crew_status": crew_status
    }

@app.post("/estimate")
async def estimate(request: EstimationRequest):
    """Run software estimation"""
    try:
        crew = get_crew()
        inputs = {
            'estimation_id': request.estimation_id,
            'project_details': request.project_details or ''
        }
        result = crew.crew().kickoff(inputs=inputs)

        return EstimationResponse(
            estimation_id=request.estimation_id,
            result=str(result),
            status="success"
        )
    except Exception as e:
        print(f"Estimation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Estimation failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Software Estimator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "status": "/api/status",
            "estimate": "/estimate"
        }
    }

def run_api():
    """Run the FastAPI server"""
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    # Use single worker to avoid multiprocessing issues with CrewAI
    workers = 1

    uvicorn.run(
        "estimator.api:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    run_api()
