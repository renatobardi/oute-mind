# oute-mind

> Multi-agent AI system for software project estimation. Powered by CrewAI and Google Gemini.

[![Deploy to GCP](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml/badge.svg)](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml)

---

## What it does

oute-mind takes a project description and produces a complete estimation report with three cost scenarios (human-only, AI-assisted, hybrid), risk analysis, and architectural recommendations. Six specialized AI agents work in sequence, each building on the previous agent's output.

```
POST /run → Agent Pipeline (90-130s) → Estimation Report (3 scenarios)
```

**Input**: project description (text, audio, video, images, documents)
**Output**: JSON report with cost scenarios, risks, timeline, and architecture

---

## Architecture

```
                          ┌─────────────────────────────────────────────┐
                          │              GCP VM (ARM64)                 │
                          │           t2a-standard-4 · 16GB             │
    Client ──── HTTP ────▶│                                             │
                          │  ┌───────┐    ┌──────────────────────────┐  │
                          │  │ Caddy │───▶│  FastAPI (estimator)     │  │
                          │  │  :80  │    │  :8000                   │  │
                          │  └───────┘    │                          │  │
                          │               │  ┌─ Agent 1: Discovery   │  │
                          │               │  ├─ Agent 2: Research    │  │
                          │               │  ├─ Agent 3: Architect   │  │
                          │               │  ├─ Agent 4: FinOps      │  │
                          │               │  ├─ Agent 5: Reviewer    │  │
                          │               │  └─ Agent 6: Knowledge   │  │
                          │               └──────────┬───────────────┘  │
                          │                          │                  │
                          │  ┌───────────┬───────────┼───────────┐     │
                          │  │           │           │           │     │
                          │  ▼           ▼           ▼           ▼     │
                          │ PostgreSQL  Redis     Qdrant     MindsDB   │
                          │  :5432      :6379     :6333      :47334    │
                          └─────────────────────────────────────────────┘
                                         │
                          External APIs  │
                          ───────────────┤
                          Gemini 2.5     │  generativelanguage.googleapis.com
                          Jina Reader    │  r.jina.ai
                          Serper         │  google.serper.dev
```

---

## Agent Pipeline

| #  | Agent                  | Role                              | Tools                                                    |
|----|------------------------|-----------------------------------|----------------------------------------------------------|
| 1  | Solution Architect     | Multi-modal discovery interview   | FileRead, OCR, ScrapeWebsite, PostgresTool, MindsDB      |
| 2  | Technical Analyst      | RAG research & web validation     | Qdrant, Serper, JinaReader, PostgresTool, MindsDB        |
| 3  | Software Architect     | Design consolidation & persist    | Qdrant, PostgresTool, MindsDB                            |
| 4  | Cost Specialist        | 3 financial scenarios             | ScrapeWebsite, PostgresTool, MindsDB                     |
| 5  | Reviewer & Presenter   | Client-facing review & approval   | Qdrant, Serper, PostgresTool, MindsDB                    |
| 6  | Knowledge Specialist   | Long-term memory enrichment       | Qdrant, PostgresTool, MindsDB                            |

Agents 1→5 run **sequentially**. Agent 6 runs at the end to enrich the knowledge base for future estimations.

Between Agent 1 and Agent 2, the system pauses for **client approval** of the discovered scope.

---

## API

| Method | Endpoint                  | Description                         |
|--------|---------------------------|-------------------------------------|
| GET    | `/health`                 | Basic health check                  |
| GET    | `/health/services`        | All 7 backend services status       |
| GET    | `/healthcheck`            | Visual health dashboard (HTML)      |
| GET    | `/api/status`             | API status + crew readiness         |
| POST   | `/run`                    | Start async estimation              |
| GET    | `/status/{estimation_id}` | Poll estimation progress            |
| POST   | `/approve/{estimation_id}`| Approve scope (after Agent 1)       |
| POST   | `/estimate`               | Synchronous estimation (blocking)   |
| GET    | `/docs`                   | Swagger UI (auto-generated)         |

### Quick test

```bash
# Health check
curl http://localhost:8000/health

# Start estimation
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"project_details": "E-commerce platform with React and FastAPI"}'

# Check status
curl http://localhost:8000/status/{estimation_id}
```

---

## Stack

| Component       | Technology              | Purpose                          |
|-----------------|-------------------------|----------------------------------|
| Orchestration   | CrewAI v1.10.1          | Agent pipeline management        |
| LLM             | Gemini 2.5 Flash-Lite   | Multi-modal reasoning            |
| Database        | PostgreSQL 16 (JSONB)   | Estimations, patterns, history   |
| Vector DB       | Qdrant                  | RAG semantic search              |
| Cache/Queue     | Redis 7                 | Async job state (TTL 24h)        |
| Memory          | MindsDB                 | Agent context synchronization    |
| Web Reader      | Jina Reader (cloud)     | Documentation extraction         |
| API             | FastAPI + Uvicorn       | REST endpoints                   |
| Reverse Proxy   | Caddy                   | HTTP routing, auto TLS           |
| Monitoring      | Prometheus + Grafana    | Metrics and dashboards           |
| CI/CD           | GitHub Actions          | Auto-deploy on push to main      |
| Infrastructure  | GCP Compute Engine      | ARM64 VM (t2a-standard-4)        |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- `GOOGLE_API_KEY` (required)
- `SERPER_API_KEY` (optional, for web search)

### Run locally

```bash
git clone https://github.com/renatobardi/oute-mind.git
cd oute-mind

# Configure
cp .env.production.example .env.production
# Edit .env.production with your API keys

# Start everything
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### Deploy to GCP

Push to `main` triggers automatic deployment via GitHub Actions.

Manual deploy:

```bash
gcloud compute ssh oute-mind --zone=us-central1-a
cd ~/oute-mind
git pull origin main
export $(cat .env.production | grep -v '^#' | xargs)
docker compose build --no-cache app
docker compose up -d app
```

---

## Configuration

```bash
# Required
GOOGLE_API_KEY=...                 # Gemini API
MODEL=google/gemini-2.5-flash-lite # LLM model

# Databases (auto-generated in production)
POSTGRES_USER=oute_prod_user
POSTGRES_PASSWORD=...
POSTGRES_DB=oute_production
REDIS_PASSWORD=...
QDRANT_API_KEY=...
QDRANT_URL=http://qdrant:6333

# Optional
SERPER_API_KEY=...                 # Web search
OCR_API_KEY=...                    # Document processing
LLM_TEMPERATURE=0.7               # 0.0-1.0
FASTAPI_WORKERS=4                  # Uvicorn workers
```

---

## Data Model

```
PostgreSQL (estimator schema)
├── estimation_requests      # Input projects
├── estimation_findings      # Agent discoveries
├── estimation_costs         # 3 cost scenarios per estimation
└── estimation_risks         # Risk assessments

Qdrant (vector collections)
├── knowledge_base           # RAG documents
├── project_patterns         # Historical patterns
├── technical_patterns       # Tech stack patterns
└── cost_history             # Past estimations
```

---

## Monitoring

| Service    | URL                        |
|------------|----------------------------|
| API Docs   | `http://<IP>:8000/docs`    |
| Health     | `http://<IP>/healthcheck`  |
| Grafana    | `http://<IP>:3080`         |
| Prometheus | `http://<IP>:9090`         |

---

## Project Structure

```
oute-mind/
├── src/estimator/
│   ├── config/
│   │   ├── agents.yaml          # Agent definitions
│   │   └── tasks.yaml           # Task definitions
│   ├── tools/
│   │   ├── postgres_tool.py     # 5 PostgreSQL tools
│   │   ├── jina_reader_tool.py  # Cloud web reader
│   │   └── mindsdb_tool.py      # Context sync tools
│   ├── crew.py                  # Pipeline orchestration
│   ├── api.py                   # FastAPI endpoints
│   ├── dashboard.html           # Health check UI
│   └── main.py                  # CLI entrypoint
├── configs/
│   ├── Caddyfile                # Reverse proxy
│   ├── postgres-init.sql        # DB schema
│   └── prometheus.yml           # Metrics config
├── app/Dockerfile               # App container
├── docker-compose.yml           # Full stack
└── reference/
    ├── DEEPWIKI.md              # Technical deep dive
    └── implementation_plan.md   # Roadmap
```

---

## Troubleshooting

| Problem                    | Fix                                                       |
|----------------------------|------------------------------------------------------------|
| OPENAI_API_KEY error       | Set any value in `.env.production` (not used, but required)|
| Gemini 404                 | Check `MODEL` env var matches available model              |
| CrewAI init fails          | Ensure `crewai[google-genai]` extra is installed           |
| Qdrant connection refused  | `docker compose logs qdrant`                               |
| Out of memory              | `docker stats` — need 16GB minimum                         |
| 504 timeout                | Increase `FASTAPI_TIMEOUT` or check Gemini rate limits     |

---

**Maintained by**: Renato Bardi
**License**: Private
