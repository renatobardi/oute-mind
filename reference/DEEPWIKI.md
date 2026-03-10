# oute-mind — Technical Deep Wiki

> Internal technical reference for the oute-mind software estimation system.
> For setup instructions, see [README.md](../README.md).

---

## System Overview

oute-mind is a **CrewAI-powered multi-agent system** that generates software project estimations. It processes requirements through a 6-agent sequential pipeline and produces three cost scenarios: human-only, AI-assisted, and hybrid.

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
│                 │  CrewAI Orchestrator                          │   │
│                 │  ┌────────────────────────────────────────┐   │   │
│                 │  │ Agent 1 ──▶ [approval] ──▶ Agent 2     │   │   │
│                 │  │ Agent 2 ──▶ Agent 3 ──▶ Agent 4       │   │   │
│                 │  │ Agent 4 ──▶ Agent 5 ──▶ Agent 6       │   │   │
│                 │  └────────────────────────────────────────┘   │   │
│                 └──────────┬──────────┬──────────┬──────────┘   │
│                            │          │          │              │
│                 ┌──────────▼──┐  ┌────▼────┐  ┌─▼──────────┐  │
│                 │ PostgreSQL  │  │  Redis   │  │   Qdrant   │  │
│                 │ 16 (JSONB)  │  │  7-alpine│  │  (vector)  │  │
│                 │ :5432       │  │  :6379   │  │  :6333     │  │
│                 └─────────────┘  └─────────┘  └────────────┘  │
│                                                                │
│                 ┌─────────────┐  ┌───────────┐  ┌──────────┐  │
│                 │  MindsDB    │  │Prometheus │  │ Grafana  │  │
│                 │  :47334     │  │  :9090    │  │ :3080    │  │
│                 └─────────────┘  └───────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
              External APIs │
              ──────────────┤
              Gemini 2.5    │ generativelanguage.googleapis.com
              Jina Reader   │ r.jina.ai (cloud API)
              Serper        │ google.serper.dev
```

### Container Map

| Container        | Image                 | Port  | Purpose                        |
|------------------|-----------------------|-------|--------------------------------|
| `oute-app`       | oute-mind-app (local) | 8000  | FastAPI + CrewAI pipeline      |
| `oute-postgres`  | postgres:16-alpine    | 5432  | Relational + JSONB storage     |
| `oute-redis`     | redis:7-alpine        | 6379  | Async job state (TTL 24h)      |
| `oute-qdrant`    | qdrant/qdrant:latest  | 6333  | Vector search / RAG            |
| `oute-mindsdb`   | mindsdb/mindsdb       | 47334 | Agent context synchronization  |
| `oute-caddy`     | caddy:latest          | 80    | Reverse proxy                  |
| `oute-prometheus` | prom/prometheus       | 9090  | Metrics collection             |
| `oute-grafana`   | grafana/grafana       | 3080  | Monitoring dashboards          |

---

## Agent Pipeline (Detail)

### Execution Model

All agents use **CrewAI sequential process**. Each agent receives the output of all previous agents as context.

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

#### Agent 1 — Solution Architect (Interviewer)

**Mission**: Multi-modal discovery interview. Extracts requirements from text, audio, video, images, and documents via Gemini's native multi-modal capabilities.

**Tools**:
| Tool              | Source     | Purpose                                  |
|-------------------|------------|------------------------------------------|
| FileReadTool      | crewai     | Read uploaded files                      |
| OCRTool           | crewai     | Extract text from images/PDFs            |
| ScrapeWebsiteTool | crewai     | Scrape reference URLs                    |
| GetChecklistTool  | custom     | Load discovery checklist from PostgreSQL |
| SaveEstimationTool| custom     | Persist findings to PostgreSQL           |
| StoreContextTool  | custom     | Share context with next agents           |

**Output**: `discovery_findings` JSON with functional requirements, non-functional requirements, constraints, and assumptions.

#### Agent 2 — Technical Research Analyst

**Mission**: Validate discoveries against RAG knowledge base and live web research. Uses Jina Reader (cloud API at r.jina.ai) for reading official documentation.

**Tools**:
| Tool                     | Source  | Purpose                              |
|--------------------------|---------|--------------------------------------|
| QdrantVectorSearchTool   | crewai  | Semantic search in knowledge base    |
| SerperDevTool            | crewai  | Google search for tech validation    |
| JinaReaderTool           | custom  | Read web docs as clean markdown      |
| SearchEstimationHistory  | custom  | Query past estimations               |
| SearchPatternsTool       | custom  | Find similar project patterns        |
| RetrieveContextTool      | custom  | Get Agent 1's discoveries            |

**Output**: `research_findings` JSON with validated technologies, risks, and reference documentation.

#### Agent 3 — Software Architect (Designer)

**Mission**: Consolidate discovery and research into a formal architecture design. Persist the design blueprint to PostgreSQL.

**Tools**: QdrantVectorSearchTool, SearchPatternsTool, SaveEstimationTool, StoreContextTool, RetrieveContextTool

**Output**: `design_blueprint` JSON with components, integrations, data model, and deployment strategy.

#### Agent 4 — Cost Optimization Specialist (FinOps)

**Mission**: Generate three financial scenarios with risk-adjusted estimates.

**Scenarios**:
1. **Human-Only**: Traditional development team
2. **AI-Assisted**: Hybrid team with AI tools (Copilot, code gen)
3. **Full AI**: Maximum AI automation with minimal human oversight

**Tools**: ScrapeWebsiteTool, SaveFinancialScenarioTool, RetrieveContextTool

**Output**: `financial_scenarios` JSON with cost breakdown, timeline, team composition, and confidence intervals.

#### Agent 5 — Reviewer & Presenter

**Mission**: Cross-validate all outputs, generate client-facing summary, and manage approval feedback loop.

**Tools**: QdrantVectorSearchTool, SerperDevTool, SearchEstimationHistoryTool, RetrieveContextTool

**Output**: Final estimation report with executive summary and recommendation.

#### Agent 6 — Knowledge Management Specialist

**Mission**: Index the completed estimation into the knowledge base for future RAG retrieval. Runs as the final step to enrich the system's memory.

**Tools**: QdrantVectorSearchTool, SaveEstimationTool, StoreContextTool

**Output**: `knowledge_enrichment` confirmation with indexed document IDs.

---

## Custom Tools

### PostgreSQL Tools (`tools/postgres_tool.py`)

| Tool                        | Operation                                    |
|-----------------------------|----------------------------------------------|
| `GetChecklistTool`          | Load discovery checklist by category         |
| `SearchEstimationHistoryTool` | Query past estimations with filters        |
| `SearchPatternsTool`        | Find technology/architecture patterns        |
| `SaveEstimationTool`        | Insert estimation findings                   |
| `SaveFinancialScenarioTool` | Insert cost scenario data                    |

Connection: `psycopg2` via env vars `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.

### Jina Reader Tool (`tools/jina_reader_tool.py`)

Cloud-only implementation using `https://r.jina.ai/{url}`. Returns web pages as clean markdown. Truncates at 15,000 characters to stay within LLM context limits.

### MindsDB Tools (`tools/mindsdb_tool.py`)

| Tool                 | Operation                                      |
|----------------------|------------------------------------------------|
| `StoreContextTool`   | Store agent output for downstream agents       |
| `RetrieveContextTool`| Retrieve upstream agent context                |

Connection: MindsDB SQL API via HTTP at `MINDSDB_HOST:MINDSDB_PORT`.

---

## API Reference

### Async Estimation Flow

```
POST /run                         → {estimation_id, status: "queued"}
GET  /status/{estimation_id}      → {status: "running", progress: "agent_2"}
POST /approve/{estimation_id}     → {status: "approved"} (after Agent 1)
GET  /status/{estimation_id}      → {status: "completed", result: {...}}
```

### All Endpoints

| Method | Path                      | Response       | Description                    |
|--------|---------------------------|----------------|--------------------------------|
| GET    | `/health`                 | JSON           | `{"status": "healthy"}`        |
| GET    | `/health/services`        | JSON           | 7 services with latency        |
| GET    | `/healthcheck`            | HTML           | Visual dashboard               |
| GET    | `/api/status`             | JSON           | Version + crew readiness       |
| GET    | `/`                       | JSON           | Available endpoints            |
| POST   | `/run`                    | JSON           | Start async estimation         |
| GET    | `/status/{id}`            | JSON           | Poll estimation status         |
| POST   | `/approve/{id}`           | JSON           | Approve Agent 1 scope          |
| POST   | `/estimate`               | JSON           | Synchronous estimation         |
| GET    | `/docs`                   | HTML           | Swagger UI (auto)              |

### Health Services Response

```json
{
  "status": "healthy",
  "services": [
    {"service": "postgresql",  "status": "ok", "latency_ms": 14, "detail": "4 tables in estimator schema"},
    {"service": "redis",       "status": "ok", "latency_ms": 3},
    {"service": "qdrant",      "status": "ok", "latency_ms": 2},
    {"service": "mindsdb",     "status": "ok", "latency_ms": 4},
    {"service": "jina_reader", "status": "ok", "latency_ms": 140, "detail": "cloud API"},
    {"service": "gemini",      "status": "ok", "latency_ms": 207},
    {"service": "crewai",      "status": "ok", "latency_ms": 0, "detail": "6 agents, 6 tasks"}
  ]
}
```

---

## Data Model

### PostgreSQL Schema (`estimator`)

```sql
estimation_requests (
    id SERIAL PRIMARY KEY,
    estimation_id VARCHAR(255) UNIQUE,
    project_details TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
)

estimation_findings (
    id SERIAL PRIMARY KEY,
    estimation_id VARCHAR(255) REFERENCES estimation_requests(estimation_id),
    agent_name VARCHAR(100),
    findings JSONB,
    created_at TIMESTAMP DEFAULT NOW()
)

estimation_costs (
    id SERIAL PRIMARY KEY,
    estimation_id VARCHAR(255) REFERENCES estimation_requests(estimation_id),
    scenario_type VARCHAR(50),   -- 'human', 'ai', 'hybrid'
    cost_breakdown JSONB,
    total_cost DECIMAL(12,2),
    timeline_weeks INTEGER,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
)

estimation_risks (
    id SERIAL PRIMARY KEY,
    estimation_id VARCHAR(255) REFERENCES estimation_requests(estimation_id),
    risk_category VARCHAR(100),
    description TEXT,
    probability DECIMAL(3,2),
    impact VARCHAR(20),
    mitigation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
```

### Qdrant Collections

| Collection           | Purpose                          | Embedding     |
|----------------------|----------------------------------|---------------|
| `knowledge_base`     | General technical knowledge      | Gemini        |
| `project_patterns`   | Past project architectures       | Gemini        |
| `technical_patterns` | Technology combinations          | Gemini        |
| `cost_history`       | Historical cost data             | Gemini        |

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

### Network Security

| Port | Service     | Access              |
|------|-------------|---------------------|
| 22   | SSH         | IP whitelist only   |
| 80   | HTTP (Caddy)| Public              |
| 443  | HTTPS       | Public (auto TLS)   |
| 5432 | PostgreSQL  | Internal only       |
| 6333 | Qdrant      | Internal only       |
| 6379 | Redis       | Internal only       |
| 47334| MindsDB     | Internal only       |

### CI/CD

GitHub Actions workflow (`.github/workflows/deploy-to-gcp.yml`):

```
Push to main → SSH to VM → git pull → docker compose build → docker compose up -d → health check
```

Secrets stored in GitHub: `GCP_VM_SSH_PRIVATE_KEY`, `GCP_VM_HOSTNAME`, `GCP_VM_USER`, `GOOGLE_API_KEY`, and database credentials.

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

## Troubleshooting

### Logs

```bash
docker compose logs app        # FastAPI + CrewAI
docker compose logs postgres   # Database
docker compose logs qdrant     # Vector DB
docker compose logs mindsdb    # Memory system
docker compose logs caddy      # Reverse proxy
```

### Common Issues

| Symptom                          | Cause                            | Fix                                      |
|----------------------------------|----------------------------------|------------------------------------------|
| `OPENAI_API_KEY` error           | CrewAI/LiteLLM requires it       | Set any `sk-proj-...` value in `.env`    |
| Gemini 404 on health check       | Wrong model in `MODEL` env var   | Use `google/gemini-2.5-flash-lite`       |
| `QdrantConfig` validation error  | Missing qdrant_config in crew.py | Ensure QDRANT_URL and QDRANT_API_KEY set |
| `google-genai` not available     | Missing pip extra                | `crewai[google-genai]` in pyproject.toml |
| OOM kills                        | Under 16GB RAM                   | Check `docker stats`, increase VM size   |
| 504 gateway timeout              | Gemini rate limit or slow agent  | Check Caddy timeout + Gemini quotas      |

---

**Version**: 1.1.0
**Maintained by**: Renato Bardi
**Last updated**: 2026-03-10
