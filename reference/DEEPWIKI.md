# oute-mind — Technical Deep Wiki

> Internal technical reference for the oute-mind software estimation system.
> For setup instructions, see [README.md](../README.md).

---

## System Overview

oute-mind is a **CrewAI-powered multi-agent system** that generates software project estimations. It processes requirements through a 6-agent sequential pipeline and produces three cost scenarios: human-only, AI-only, and hybrid.

**Target users**: software companies, consultancies, enterprise IT teams needing accurate project cost forecasting.

**Core flow**:
```
Client Request → 6-Agent Pipeline (90-130s) → 3 Cost Scenarios + Risks + Architecture
```

---

## Architecture

### System Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GCP Compute Engine                              │
│                     t2a-standard-4 (ARM64)                          │
│                     16GB RAM · 4 vCPU                               │
│                                                                     │
│  ┌──────────┐   ┌──────────────────────────────────────────────┐   │
│  │  Caddy   │──▶│           FastAPI Application                │   │
│  │  :80     │   │           (estimator.api)                    │   │
│  └──────────┘   │                                              │   │
│                 │  CrewAI Orchestrator (sequential)             │   │
│                 │  ┌────────────────────────────────────────┐   │   │
│                 │  │ Agent 1 ──▶ [approval] ──▶ Agent 2     │   │   │
│                 │  │ Agent 2 ──▶ Agent 3 ──▶ Agent 4       │   │   │
│                 │  │ Agent 4 ──▶ Agent 5 ──▶ Agent 6       │   │   │
│                 │  └────────────────────────────────────────┘   │   │
│                 └───────────┬──────┬──────┬──────┬──────────┘   │
│                             │      │      │      │              │
│                 ┌───────────▼──┐ ┌─▼────┐ ┌▼─────────┐ ┌──▼──────┐│
│                 │ PostgreSQL   │ │Redis │ │ Qdrant   │ │MindsDB  ││
│                 │ 16 (JSONB)   │ │7-alp │ │ (vector) │ │         ││
│                 │ :5432        │ │:6379 │ │ :6333    │ │:47334   ││
│                 └──────────────┘ └──────┘ └──────────┘ └─────────┘│
│                                                                    │
│                 ┌──────────────┐  ┌──────────────┐                │
│                 │ Prometheus   │  │  Grafana     │                │
│                 │ :9090        │  │  :3080       │                │
│                 └──────────────┘  └──────────────┘                │
└────────────────────────────────────────────────────────────────────┘
                           │
             External APIs │
             ──────────────┤
             Gemini 2.5    │ generativelanguage.googleapis.com
             Jina Reader   │ r.jina.ai (cloud API, no container)
             Serper        │ google.serper.dev
```

### Container Map

| Container          | Image                   | Port(s)     | Purpose                        |
|--------------------|-------------------------|-------------|--------------------------------|
| `oute-app`         | oute-mind-app (local)   | 8000        | FastAPI + CrewAI pipeline      |
| `oute-postgres`    | postgres:16-alpine      | 5432        | Relational + JSONB storage     |
| `oute-redis`       | redis:7-alpine          | 6379        | Async job state (TTL 24h)      |
| `oute-qdrant`      | qdrant/qdrant:latest    | 6333, 6334  | Vector search / RAG            |
| `oute-mindsdb`     | mindsdb/mindsdb:latest  | 47334, 47335| Agent context synchronization  |
| `oute-caddy`       | caddy:latest            | 80          | Reverse proxy                  |
| `oute-prometheus`  | prom/prometheus:latest  | 9090        | Metrics collection             |
| `oute-grafana`     | grafana/grafana:latest  | 3080        | Monitoring dashboards          |

Additional `oute-main` services (when available): `oute-dashboard` (:3020), `oute-auth-profile` (:3021), `oute-projects` (:3022).

### Caddy Routing

| Path             | Target                     |
|------------------|----------------------------|
| `/dashboard*`    | `http://00_dashboard:3000` |
| `/api/auth*`     | `http://01_auth-profile:3001` |
| `/api/projects*` | `http://02_projects:3002`  |
| `/*` (default)   | `http://app:8000`          |

---

## Agent Pipeline (Detail)

### Execution Model

All agents use **CrewAI sequential process** (`Process.sequential`). Each agent receives the output of all previous agents as context. LLM: `google/gemini-2.5-flash-lite` (configurable via `MODEL` env var). Temperature: `0.7` (configurable via `LLM_TEMPERATURE`).

```
Agent 1 (Discovery)
    │
    ▼
[Client Approval Gate]     ← human_input=True
    │
    ▼
Agent 2 (Research)
    │
    ▼
Agent 3 (Architecture)
    │
    ▼
Agent 4 (Cost Modeling)
    │
    ▼
Agent 5 (Review)           ← human_input=True
    │
    ▼
Agent 6 (Knowledge)
```

### Agent Specifications

#### Agent 1 — `software_architecture_interviewer`

**Role**: Solution Architect
**Mission**: Multi-modal discovery interview. Extracts requirements from text, audio, video, images, and documents via Gemini's native multi-modal capabilities.

| Tool                 | Source     | Purpose                                  |
|----------------------|------------|------------------------------------------|
| `FileReadTool`       | crewai     | Read uploaded files                      |
| `OCRTool`            | crewai     | Extract text from images/PDFs            |
| `ScrapeWebsiteTool`  | crewai     | Scrape reference URLs                    |
| `GetChecklistTool`   | custom     | Load discovery checklist from PostgreSQL |
| `SaveEstimationTool` | custom     | Persist findings to PostgreSQL           |
| `StoreContextTool`   | custom     | Share context with next agents via MindsDB|

**Output**: `discovery_findings` — functional requirements, non-functional requirements, constraints, assumptions.

#### Agent 2 — `technical_research_analyst_with_rag`

**Role**: Technical Research Analyst
**Mission**: Validate discoveries against RAG knowledge base and live web research. Uses Jina Reader cloud API (r.jina.ai) for reading official documentation as clean markdown.

| Tool                          | Source  | Purpose                              |
|-------------------------------|---------|--------------------------------------|
| `QdrantVectorSearchTool`      | crewai  | Semantic search in `knowledge_base`  |
| `SerperDevTool`               | crewai  | Google search for tech validation    |
| `JinaReaderTool`              | custom  | Read web docs via r.jina.ai          |
| `SearchEstimationHistoryTool` | custom  | Query past estimations               |
| `SearchPatternsTool`          | custom  | Find similar design patterns         |
| `RetrieveContextTool`         | custom  | Get Agent 1's context from MindsDB   |

**Output**: `research_findings` — validated technologies, risks, reference docs.

#### Agent 3 — `software_architect`

**Role**: Software Architect & Designer
**Mission**: Consolidate discovery and research into a formal architecture design. Persist the blueprint to PostgreSQL.

| Tool                          | Source  | Purpose                              |
|-------------------------------|---------|--------------------------------------|
| `QdrantVectorSearchTool`      | crewai  | Search similar architectures         |
| `SearchPatternsTool`          | custom  | Find reusable design patterns        |
| `SaveEstimationTool`          | custom  | Persist design to PostgreSQL         |
| `StoreContextTool`            | custom  | Share design with downstream agents  |
| `RetrieveContextTool`         | custom  | Get upstream agent context           |

**Output**: `design_blueprint` — components, integrations, data model, deployment.

#### Agent 4 — `cost_optimization_specialist`

**Role**: FinOps Specialist
**Mission**: Generate three financial scenarios with risk-adjusted estimates.

| Scenario       | Description                                         |
|----------------|-----------------------------------------------------|
| `human-only`   | Traditional development team                        |
| `ai-only`      | Maximum AI automation, minimal human oversight      |
| `hybrid`       | Balanced team with AI tools (Copilot, code gen)     |

| Tool                          | Source  | Purpose                              |
|-------------------------------|---------|--------------------------------------|
| `ScrapeWebsiteTool`           | crewai  | Research market rates                |
| `SaveFinancialScenarioTool`   | custom  | Persist scenarios to PostgreSQL      |
| `RetrieveContextTool`         | custom  | Get architecture from Agent 3        |

**Output**: `financial_scenarios` — cost breakdown, timeline, team, confidence.

#### Agent 5 — `reviewer_and_presenter`

**Role**: Technical-Functional Reviewer
**Mission**: Cross-validate all outputs, generate client-facing summary, and manage approval feedback loop.

| Tool                          | Source  | Purpose                              |
|-------------------------------|---------|--------------------------------------|
| `QdrantVectorSearchTool`      | crewai  | Validate against knowledge base      |
| `SerperDevTool`               | crewai  | Additional research if needed        |
| `SearchEstimationHistoryTool` | custom  | Compare with past estimations        |
| `RetrieveContextTool`         | custom  | Get all upstream context             |

**Output**: Final estimation report with executive summary and recommendation.

#### Agent 6 — `knowledge_management_specialist`

**Role**: Knowledge Guardian
**Mission**: Index the completed estimation into the knowledge base for future RAG retrieval.

| Tool                          | Source  | Purpose                              |
|-------------------------------|---------|--------------------------------------|
| `QdrantVectorSearchTool`      | crewai  | Check for duplicates before indexing |
| `SaveEstimationTool`          | custom  | Persist enrichment to PostgreSQL     |
| `StoreContextTool`            | custom  | Store completion confirmation        |

**Output**: `knowledge_enrichment` — indexed document confirmation.

---

## Custom Tools

### PostgreSQL Tools (`src/estimator/tools/postgres_tool.py`)

All tools connect via `psycopg2` using env vars: `POSTGRES_HOST` (default: `postgres`), `POSTGRES_PORT` (default: `5432`), `POSTGRES_USER` (default: `oute_prod_user`), `POSTGRES_PASSWORD`, `POSTGRES_DB` (default: `oute_production`).

| Class Name                    | Tool Name                   | Schema Table              | Operation |
|-------------------------------|-----------------------------|---------------------------|-----------|
| `GetChecklistTool`            | "Get Discovery Checklist"   | `estimator.checklists`    | SELECT by phase |
| `SearchEstimationHistoryTool` | "Search Estimation History" | `estimator.estimation_history` | SELECT with filters |
| `SearchPatternsTool`          | "Search Design Patterns"    | `estimator.patterns`      | SELECT by name/keyword |
| `SaveEstimationTool`          | "Save Estimation Results"   | `estimator.estimation_history` | INSERT |
| `SaveFinancialScenarioTool`   | "Save Financial Scenario"   | `estimator.financial_scenarios` | INSERT |

### Jina Reader Tool (`src/estimator/tools/jina_reader_tool.py`)

| Class Name      | Tool Name                      | Endpoint                  |
|-----------------|--------------------------------|---------------------------|
| `JinaReaderTool`| "Read Web Page (Jina Reader)"  | `https://r.jina.ai/{url}` |

Cloud-only. Returns web pages as clean markdown. Truncates at 15,000 characters. Header: `Accept: text/markdown`. Timeout: 30s.

### MindsDB Tools (`src/estimator/tools/mindsdb_tool.py`)

All tools connect via HTTP to `MINDSDB_HOST:MINDSDB_PORT` (default: `mindsdb:47334`). Uses SQL API endpoint `POST /api/sql/query`. Internal table: `agent_context` (columns: `key_name`, `agent_name`, `context_data`, `created_at`).

| Class Name           | Tool Name                | Operation                           |
|----------------------|--------------------------|-------------------------------------|
| `StoreContextTool`   | "Store Agent Context"    | INSERT/UPDATE agent_context         |
| `RetrieveContextTool`| "Retrieve Agent Context" | SELECT from agent_context by key    |

Context keys used across agents: `discovery_findings`, `design_blueprint`, `knowledge_enrichment`, `rag_validation`.

---

## API Reference

### Async Estimation Flow

```
POST /run                         → {estimation_id, status: "queued"}
GET  /status/{estimation_id}      → {status: "running", current_phase: 2, phase_name: "RAG Analysis"}
POST /approve/{estimation_id}     → {status: "approved"}
GET  /status/{estimation_id}      → {status: "completed", result: {...}}
```

### All Endpoints

| Method | Path                      | Response       | Description                    |
|--------|---------------------------|----------------|--------------------------------|
| GET    | `/`                       | JSON           | Available endpoints list       |
| GET    | `/health`                 | JSON           | Lightweight (no crew init)     |
| GET    | `/health/services`        | JSON           | 7 services with latency        |
| GET    | `/healthcheck`            | HTML           | Visual dashboard               |
| GET    | `/api/status`             | JSON           | Version + crew readiness       |
| POST   | `/run`                    | `RunResponse`  | Start async estimation         |
| GET    | `/status/{id}`            | `StatusResponse`| Poll estimation status        |
| POST   | `/approve/{id}`           | JSON           | Approve Agent 1 scope          |
| POST   | `/estimate`               | `EstimationResponse` | Synchronous estimation   |
| GET    | `/docs`                   | HTML (auto)    | Swagger UI                     |

### Response Models

```python
class RunResponse:
    estimation_id: str
    status: str          # "queued"
    message: str

class StatusResponse:
    estimation_id: str
    status: str          # "queued" | "running" | "completed" | "failed"
    current_phase: int   # 1-6
    phase_name: str      # e.g. "Discovery (Interviewer)"
    started_at: str
    completed_at: str
    result: str          # final output (when completed)
    error: str           # error message (when failed)

class EstimationResponse:
    estimation_id: str
    result: str
    status: str          # "success"
```

### Phase Names

| Phase | Name                                   |
|-------|----------------------------------------|
| 1     | Discovery (Interviewer)                |
| 2     | RAG Analysis (Researcher)              |
| 3     | Design & Persistence (Architect)       |
| 4     | Financial Scenarios (Cost Specialist)  |
| 5     | Review & Presentation (Reviewer)       |
| 6     | Knowledge Enrichment (Knowledge Spec.) |

### Health Services Response

```json
{
  "status": "healthy",
  "services": [
    {"service": "postgresql",  "status": "ok", "latency_ms": 14, "detail": "4 tables in estimator schema"},
    {"service": "redis",       "status": "ok", "latency_ms": 3},
    {"service": "qdrant",      "status": "ok", "latency_ms": 2, "detail": "healthz check passed"},
    {"service": "mindsdb",     "status": "ok", "latency_ms": 4},
    {"service": "jina_reader", "status": "ok", "latency_ms": 140, "detail": "cloud API"},
    {"service": "gemini",      "status": "ok", "latency_ms": 207, "detail": "OK"},
    {"service": "crewai",      "status": "ok", "latency_ms": 0, "detail": "6 agents, 6 tasks"}
  ]
}
```

---

## Data Model

### PostgreSQL Schema (`estimator`)

```sql
-- Discovery checklists (Agent 1)
estimator.checklists (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    phase VARCHAR(50),           -- 'initial_scoping', 'technical_deep_dive', 'integration_review'
    content JSONB NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP         -- auto-trigger
)

-- Agent findings per project (Agents 1-6)
estimator.estimation_history (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,
    phase INT,                   -- 1 through 6
    status VARCHAR(50),          -- 'completed', 'in_progress', 'approved', 'pending_approval'
    data JSONB NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP         -- auto-trigger
)

-- Reusable design patterns (Agent 3, 6)
estimator.patterns (
    id UUID PRIMARY KEY,
    pattern_name VARCHAR(255) UNIQUE,
    description TEXT,
    pattern_data JSONB NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP         -- auto-trigger
)

-- Cost scenarios (Agent 4)
estimator.financial_scenarios (
    id UUID PRIMARY KEY,
    estimation_id UUID NOT NULL,
    scenario_type VARCHAR(50),   -- 'human-only', 'ai-only', 'hybrid'
    costs JSONB NOT NULL,
    timeline JSONB NOT NULL,
    risks JSONB NOT NULL,
    created_at TIMESTAMP
)
```

**Indexes**: `project_id` on checklists and estimation_history, `team_id` on estimation_history, `pattern_name` on patterns, `estimation_id` on financial_scenarios.

**Extensions**: `uuid-ossp` (UUID generation), `pg_trgm` (trigram matching).

### Qdrant

| Collection       | Purpose                                     |
|------------------|---------------------------------------------|
| `knowledge_base` | RAG documents for semantic search (default) |

Collection name configurable via `QDRANT_COLLECTION` env var (default: `knowledge_base`). Connected via `QdrantConfig` with `QDRANT_URL` and `QDRANT_API_KEY`.

### Redis

Job state stored as JSON with 24-hour TTL. Key format: `job:{estimation_id}`.

Fields: `status`, `current_phase`, `phase_name`, `started_at`, `completed_at`, `result`, `error`.

### MindsDB

Internal table `agent_context` for inter-agent communication. Not persistent across restarts — used only during active estimation runs.

---

## Infrastructure

### GCP Setup

| Resource          | Spec                             |
|-------------------|----------------------------------|
| VM                | t2a-standard-4 (ARM64)           |
| CPU               | 4 vCPU (Ampere Altra)            |
| RAM               | 16 GB                            |
| Disk              | 50 GB SSD                        |
| OS                | Ubuntu 22.04 LTS                 |
| Region            | us-central1-a                    |
| Static IP         | oute-mind-ip                     |
| Est. cost         | ~$120/month                      |

### Memory Budget (16GB)

```
FastAPI + CrewAI:  ~1.0 GB
PostgreSQL:        ~3.0 GB
Redis:             ~0.5 GB
Qdrant:            ~2.0 GB
MindsDB:           ~1.0 GB
Prometheus:        ~0.5 GB
Grafana:           ~0.5 GB
Caddy:             ~0.1 GB
System (OS):       ~2.0 GB
Buffer:            ~5.4 GB
```

Jina Reader is cloud-only (r.jina.ai) — no local container, no memory usage.

### Network Security

| Port   | Service      | Access              |
|--------|-------------|---------------------|
| 22     | SSH          | IP whitelist only   |
| 80     | HTTP (Caddy) | Public              |
| 443    | HTTPS        | Public (auto TLS)   |
| 5432   | PostgreSQL   | Internal only       |
| 6333   | Qdrant       | Internal only       |
| 6379   | Redis        | Internal only       |
| 47334  | MindsDB      | Internal only       |

### CI/CD

GitHub Actions workflow (`.github/workflows/deploy-to-gcp.yml`):

```
Push to main → SSH to VM → git pull → docker compose build → docker compose up -d → curl /health
```

Secrets stored in GitHub: `GCP_VM_SSH_PRIVATE_KEY`, `GCP_VM_SSH_KNOWN_HOSTS`, `GCP_VM_USER`, `GCP_VM_HOSTNAME`, `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT_KEY`, `GOOGLE_API_KEY`, `SERPER_API_KEY`, `COMPOSIO_API_KEY`, `OCR_API_KEY`, `QDRANT_API_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `MINDSDB_ADMIN_PASSWORD`, `GRAFANA_PASSWORD`.

---

## Performance

### Expected Latencies

| Agent              | Time  |
|--------------------|-------|
| 1. Discovery       | ~30s  |
| 2. Research        | ~40s  |
| 3. Architecture    | ~25s  |
| 4. Cost            | ~15s  |
| 5. Review          | ~20s  |
| 6. Knowledge       | ~30s  |
| **Total Pipeline** | **90-130s** |

### Capacity

- Concurrent estimations: 5-10
- Bottleneck: Gemini API rate limits (RPM)
- Max request payload: 10MB

---

## Monitoring

### Prometheus Scrape Targets

| Job             | Target                    | Interval |
|-----------------|---------------------------|----------|
| prometheus      | localhost:9090            | 15s      |
| caddy           | caddy:80                  | 15s      |
| fastapi         | app:8000                  | 15s      |
| redis           | redis:6379                | 15s      |
| postgresql      | postgres:5432             | 15s      |
| qdrant          | qdrant:6333               | 15s      |
| oute-dashboard  | 00_dashboard:3000         | 15s      |
| oute-auth       | 01_auth-profile:3001      | 15s      |
| oute-projects   | 02_projects:3002          | 15s      |

### Logs

```bash
docker compose logs app        # FastAPI + CrewAI
docker compose logs postgres   # Database
docker compose logs qdrant     # Vector DB
docker compose logs mindsdb    # Memory system
docker compose logs caddy      # Reverse proxy
```

---

## Troubleshooting

| Symptom                          | Cause                            | Fix                                      |
|----------------------------------|----------------------------------|------------------------------------------|
| `OPENAI_API_KEY` error           | CrewAI/LiteLLM requires it       | Set any `sk-proj-...` value in `.env`    |
| Gemini 404 on health check       | Wrong model in `MODEL` env var   | Use `google/gemini-2.5-flash-lite`       |
| `QdrantConfig` validation error  | Missing qdrant_config in crew.py | Ensure `QDRANT_URL` and `QDRANT_API_KEY` |
| `google-genai` not available     | Missing pip extra                | `crewai[google-genai]` in pyproject.toml |
| OOM kills                        | Under 16GB RAM                   | Check `docker stats`, increase VM size   |
| 504 gateway timeout              | Gemini rate limit or slow agent  | Check Caddy timeout + Gemini quotas      |
| MindsDB connection refused       | Container not ready              | `docker compose logs mindsdb`, wait      |
| PostgreSQL permission denied     | Wrong credentials                | Match `.env.production` with compose     |

---

## Dependencies

```toml
crewai[litellm,tools,google-genai]==1.10.1
minds-sdk
qdrant-client
psycopg2-binary>=2.9.0
requests>=2.31.0
redis>=5.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
```

Python: `>=3.10, <3.14`. Dockerfile base: `python:3.13-slim`.

---

**Version**: 1.1.0
**Maintained by**: Renato Bardi
**Last updated**: 2026-03-10
