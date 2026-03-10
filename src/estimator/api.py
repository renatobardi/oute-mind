#!/usr/bin/env python
"""FastAPI wrapper for CrewAI software estimator with async execution."""

import os
import json
import uuid
import threading
from datetime import datetime, timezone

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
import uvicorn
import redis
import requests as http_requests
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from estimator.crew import SoftwareProjectEstimatorWithRagCrew

# Create FastAPI app
app = FastAPI(
    title="Software Estimator API",
    description="CrewAI-powered software project estimation API with async execution",
    version="1.1.0"
)


# --- Redis connection ---

def _get_redis() -> redis.Redis:
    """Get Redis connection for job state management."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True,
    )


def _set_job_state(estimation_id: str, state: dict):
    """Persist job state to Redis with 24h TTL."""
    r = _get_redis()
    r.setex(f"job:{estimation_id}", 86400, json.dumps(state, default=str))


def _get_job_state(estimation_id: str) -> dict | None:
    """Retrieve job state from Redis."""
    r = _get_redis()
    data = r.get(f"job:{estimation_id}")
    return json.loads(data) if data else None


# --- Pydantic Models ---

class RunRequest(BaseModel):
    project_details: str
    estimation_id: str | None = None

class RunResponse(BaseModel):
    estimation_id: str
    status: str
    message: str

class ApproveRequest(BaseModel):
    approved: bool = True
    feedback: str | None = None

class StatusResponse(BaseModel):
    estimation_id: str
    status: str
    current_phase: int | None = None
    phase_name: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: str | None = None
    error: str | None = None

class EstimationRequest(BaseModel):
    estimation_id: str
    project_details: str | None = None

class EstimationResponse(BaseModel):
    estimation_id: str
    result: str
    status: str = "success"


# --- Lazy crew initialization ---

_crew_instance = None

def get_crew():
    """Lazy load the crew instance."""
    global _crew_instance
    if _crew_instance is None:
        try:
            _crew_instance = SoftwareProjectEstimatorWithRagCrew()
        except Exception as e:
            print(f"Warning: Failed to initialize crew: {e}")
            raise
    return _crew_instance


# --- Phase definitions ---

PHASES = {
    1: "Discovery (Interviewer)",
    2: "RAG Analysis (Researcher)",
    3: "Design & Persistence (Architect)",
    4: "Financial Scenarios (Cost Specialist)",
    5: "Review & Presentation (Reviewer)",
    6: "Knowledge Enrichment (Knowledge Specialist)",
}


# --- Background worker ---

def _run_estimation_worker(estimation_id: str, project_details: str):
    """Run the CrewAI estimation pipeline in a background thread."""
    try:
        _set_job_state(estimation_id, {
            "status": "running",
            "current_phase": 1,
            "phase_name": PHASES[1],
            "started_at": datetime.now(timezone.utc).isoformat(),
        })

        crew = get_crew()
        inputs = {
            "estimation_id": estimation_id,
            "project_details": project_details,
        }

        # Phase 1 requires human approval — check if approval flow is needed
        # For now, run the full pipeline; approval gate is handled via /approve
        state = _get_job_state(estimation_id)
        if state and state.get("status") == "awaiting_approval":
            return  # Wait for approval before continuing

        result = crew.crew().kickoff(inputs=inputs)

        _set_job_state(estimation_id, {
            "status": "completed",
            "current_phase": 6,
            "phase_name": PHASES[6],
            "started_at": state.get("started_at") if state else None,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": str(result),
        })

    except Exception as e:
        _set_job_state(estimation_id, {
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })


# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint — lightweight, no crew init."""
    return {
        "status": "healthy",
        "service": "software-estimator"
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    try:
        crew = get_crew()
        crew_status = "ready"
    except Exception:
        crew_status = "initializing"

    return {
        "status": "running",
        "service": "software-estimator",
        "version": "1.1.0",
        "crew_status": crew_status
    }


@app.get("/")
async def root():
    """Root endpoint with available routes."""
    return {
        "message": "Software Estimator API",
        "version": "1.1.0",
        "endpoints": {
            "health": "GET /health",
            "status": "GET /api/status",
            "run": "POST /run",
            "approve": "POST /approve/{estimation_id}",
            "job_status": "GET /status/{estimation_id}",
            "estimate_sync": "POST /estimate",
        }
    }


@app.post("/run", response_model=RunResponse)
async def run_estimation(request: RunRequest):
    """Start an async estimation. Returns immediately with an estimation ID."""
    estimation_id = request.estimation_id or str(uuid.uuid4())

    # Check if already running
    existing = _get_job_state(estimation_id)
    if existing and existing.get("status") in ("running", "awaiting_approval"):
        raise HTTPException(
            status_code=409,
            detail=f"Estimation '{estimation_id}' is already {existing['status']}."
        )

    # Initialize job state
    _set_job_state(estimation_id, {
        "status": "queued",
        "current_phase": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })

    # Launch background worker
    worker = threading.Thread(
        target=_run_estimation_worker,
        args=(estimation_id, request.project_details),
        daemon=True,
        name=f"estimation-{estimation_id}",
    )
    worker.start()

    return RunResponse(
        estimation_id=estimation_id,
        status="queued",
        message=f"Estimation started. Check progress at GET /status/{estimation_id}",
    )


@app.get("/status/{estimation_id}", response_model=StatusResponse)
async def get_estimation_status(estimation_id: str):
    """Check the progress of an async estimation."""
    state = _get_job_state(estimation_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Estimation '{estimation_id}' not found."
        )

    return StatusResponse(
        estimation_id=estimation_id,
        status=state.get("status", "unknown"),
        current_phase=state.get("current_phase"),
        phase_name=state.get("phase_name"),
        started_at=state.get("started_at"),
        completed_at=state.get("completed_at"),
        result=state.get("result"),
        error=state.get("error"),
    )


@app.post("/approve/{estimation_id}")
async def approve_estimation(estimation_id: str, request: ApproveRequest):
    """Approve or reject the discovery phase to continue the pipeline."""
    state = _get_job_state(estimation_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Estimation '{estimation_id}' not found."
        )

    if state.get("status") != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Estimation is not awaiting approval. Current status: {state.get('status')}"
        )

    if not request.approved:
        _set_job_state(estimation_id, {
            **state,
            "status": "rejected",
            "feedback": request.feedback,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"estimation_id": estimation_id, "status": "rejected", "message": "Estimation rejected by client."}

    # Approved — resume pipeline from phase 2
    _set_job_state(estimation_id, {
        **state,
        "status": "running",
        "current_phase": 2,
        "phase_name": PHASES[2],
        "feedback": request.feedback,
    })

    # Re-launch worker to continue from phase 2
    worker = threading.Thread(
        target=_run_estimation_worker,
        args=(estimation_id, state.get("project_details", "")),
        daemon=True,
        name=f"estimation-resume-{estimation_id}",
    )
    worker.start()

    return {
        "estimation_id": estimation_id,
        "status": "approved",
        "message": "Discovery approved. Pipeline resuming from RAG analysis.",
    }


# --- Service Health Checks ---

def _check_service(name: str, check_fn) -> dict:
    """Run a health check function and return status dict."""
    try:
        start = datetime.now(timezone.utc)
        result = check_fn()
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        return {"service": name, "status": "ok", "latency_ms": round(elapsed * 1000), "detail": result}
    except Exception as e:
        return {"service": name, "status": "error", "detail": str(e)}


@app.get("/health/services")
async def health_services():
    """Check connectivity to all backend services."""
    checks = []

    # PostgreSQL
    def check_postgres():
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "oute_prod_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "oute_production"),
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'estimator'")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return f"{count} tables in estimator schema"
    checks.append(_check_service("postgresql", check_postgres))

    # Redis
    def check_redis():
        r = _get_redis()
        return r.ping()
    checks.append(_check_service("redis", check_redis))

    # Qdrant
    def check_qdrant():
        url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        resp = http_requests.get(f"{url}/healthz", timeout=5)
        resp.raise_for_status()
        return resp.text.strip()
    checks.append(_check_service("qdrant", check_qdrant))

    # MindsDB
    def check_mindsdb():
        host = os.getenv("MINDSDB_HOST", "mindsdb")
        port = os.getenv("MINDSDB_PORT", "47334")
        resp = http_requests.get(f"http://{host}:{port}/api/status", timeout=5)
        resp.raise_for_status()
        return resp.json()
    checks.append(_check_service("mindsdb", check_mindsdb))

    # Jina Reader (cloud API: r.jina.ai)
    def check_jina():
        resp = http_requests.get("https://r.jina.ai/https://example.com", headers={"Accept": "text/markdown"}, timeout=10)
        resp.raise_for_status()
        return f"cloud API ({len(resp.text)} chars)"
    checks.append(_check_service("jina_reader", check_jina))

    # Google Gemini
    def check_gemini():
        api_key = os.getenv("GOOGLE_API_KEY", "")
        # Extract model name from MODEL env var (format: "google/gemini-2.5-flash-lite" -> "gemini-2.5-flash-lite")
        model = os.getenv("MODEL", "gemini-2.5-flash-lite").split("/")[-1]
        resp = http_requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": "Reply with only: OK"}]}]},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return text.strip()
    checks.append(_check_service("gemini", check_gemini))

    # CrewAI
    def check_crewai():
        crew = get_crew()
        agent_count = len(crew.crew().agents)
        task_count = len(crew.crew().tasks)
        return f"{agent_count} agents, {task_count} tasks"
    checks.append(_check_service("crewai", check_crewai))

    # --- Infrastructure ---

    # Prometheus
    def check_prometheus():
        resp = http_requests.get("http://prometheus:9090/-/healthy", timeout=5)
        resp.raise_for_status()
        return resp.text.strip()
    checks.append(_check_service("prometheus", check_prometheus))

    # Grafana
    def check_grafana():
        resp = http_requests.get("http://grafana:3000/api/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    checks.append(_check_service("grafana", check_grafana))

    # Caddy (use admin API — port 80 proxies back to this app, causing deadlock)
    def check_caddy():
        resp = http_requests.get("http://caddy:2019/config/", timeout=5)
        resp.raise_for_status()
        return "admin API reachable"
    checks.append(_check_service("caddy", check_caddy))

    # --- oute-main services ---

    # Dashboard
    def check_dashboard():
        resp = http_requests.get("http://00_dashboard:3000/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    checks.append(_check_service("dashboard", check_dashboard))

    # Auth Profile
    def check_auth():
        resp = http_requests.get("http://01_auth-profile:3001/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    checks.append(_check_service("auth_profile", check_auth))

    # Projects
    def check_projects():
        resp = http_requests.get("http://02_projects:3002/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    checks.append(_check_service("projects", check_projects))

    all_ok = all(c["status"] == "ok" for c in checks)
    return {"status": "healthy" if all_ok else "degraded", "services": checks}


@app.get("/healthcheck", response_class=HTMLResponse)
async def healthcheck_page():
    """Service health dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(html_path, "r") as f:
        return f.read()


@app.post("/estimate", response_model=EstimationResponse)
async def estimate(request: EstimationRequest):
    """Run software estimation synchronously (legacy endpoint)."""
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


def run_api():
    """Run the FastAPI server."""
    port = int(os.getenv("FASTAPI_PORT", "8000"))

    uvicorn.run(
        "estimator.api:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    run_api()
