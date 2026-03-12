# oute-mind

> Multi-agent AI system for software project estimation. Powered by CrewAI and Google Gemini.

[![Deploy to GCP](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml/badge.svg)](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml)

---

## What it does

oute-mind takes a project description and produces a complete estimation report with three cost scenarios (human-only, AI-only, hybrid), risk analysis, and architectural recommendations. Six specialized AI agents work in sequence, each building on the previous agent's output.

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
                          │  │  :80  │    │  :8000 (internal only)   │  │
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

| #  | Agent                  | Role                              | Tools                                                              |
|----|------------------------|-----------------------------------|--------------------------------------------------------------------|
| 1  | Solution Architect     | Multi-modal discovery interview   | FileRead, OCR, ScrapeWebsite, GetChecklist, SaveEstimation, StoreContext |
| 2  | Technical Analyst      | RAG research & web validation     | QdrantVectorSearch, Serper, JinaReader, SearchHistory, SearchPatterns, RetrieveContext |
| 3  | Software Architect     | Design consolidation & persist    | QdrantVectorSearch, SearchPatterns, SaveEstimation, StoreContext, RetrieveContext |
| 4  | Cost Specialist        | 3 financial scenarios             | ScrapeWebsite, SaveFinancialScenario, RetrieveContext              |
| 5  | Reviewer & Presenter   | Client-facing review & approval   | QdrantVectorSearch, Serper, SearchHistory, RetrieveContext          |
| 6  | Knowledge Specialist   | Long-term memory enrichment       | QdrantVectorSearch, SaveEstimation, StoreContext                   |

Agents 1→6 run **sequentially**. Between Agent 1 and Agent 2, the system pauses for **client approval** of the discovered scope (`human_input=True`). Agent 5 also requires human input for final review.

---

## API

| Method | Endpoint                  | Description                         |
|--------|---------------------------|-------------------------------------|
| GET    | `/health`                 | Lightweight health check            |
| GET    | `/health/services`        | All 7 backend services status       |
| GET    | `/healthcheck`            | Visual health dashboard (HTML)      |
| GET    | `/api/status`             | API version + crew readiness        |
| POST   | `/run`                    | Start async estimation              |
| GET    | `/status/{estimation_id}` | Poll estimation progress            |
| POST   | `/approve/{estimation_id}`| Approve scope (after Agent 1)       |
| POST   | `/estimate`               | Synchronous estimation (blocking)   |
| GET    | `/docs`                   | Swagger UI (auto-generated)         |

### Quick test

```bash
# Health check (via Caddy reverse proxy)
curl http://localhost/health

# Start estimation (via Caddy reverse proxy)
curl -X POST http://localhost/run \
  -H "Content-Type: application/json" \
  -d '{"project_details": "E-commerce platform with React and FastAPI"}'

# Check status (via Caddy reverse proxy)
curl http://localhost/status/{estimation_id}
```

---

## Stack

| Component       | Technology              | Purpose                          |
|-----------------|-------------------------|----------------------------------|
| Orchestration   | CrewAI v1.10.1          | Agent pipeline management        |
| LLM             | Gemini 2.5 Flash-Lite   | Multi-modal reasoning            |
| Database        | PostgreSQL 16 (JSONB)   | Checklists, history, patterns    |
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
curl http://localhost/health
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
OPENAI_API_KEY=sk-proj-...        # Required by CrewAI/LiteLLM (not used for requests)

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

### PostgreSQL (`estimator` schema)

| Table                  | Purpose                                    |
|------------------------|--------------------------------------------|
| `checklists`           | Discovery checklists by phase (JSONB)      |
| `estimation_history`   | Agent findings per project/team/phase      |
| `patterns`             | Reusable design patterns (JSONB)           |
| `financial_scenarios`  | Cost scenarios: human-only, ai-only, hybrid|

### Qdrant

| Collection       | Purpose                                     |
|------------------|---------------------------------------------|
| `knowledge_base` | RAG documents for semantic search           |

---

## Monitoring

| Service    | URL / Access                                              |
|------------|-----------------------------------------------------------|
| API Docs   | `http://<IP>/docs` (via Caddy)                            |
| Health     | `http://<IP>/healthcheck` (via Caddy)                     |
| Grafana    | Internal only — access via `docker exec` or SSH tunnel    |
| Prometheus | Internal only — access via `docker exec` or SSH tunnel    |

> **Note**: Grafana and Prometheus are not exposed on host ports. To access them, use an SSH tunnel:
> ```bash
> # Grafana (internal port 3000)
> gcloud compute ssh oute-mind --zone=us-central1-a -- -L 3080:grafana:3000
> # Then open http://localhost:3080 in your browser
>
> # Prometheus (internal port 9090)
> gcloud compute ssh oute-mind --zone=us-central1-a -- -L 9090:prometheus:9090
> # Then open http://localhost:9090 in your browser
> ```

---

## Project Structure

```
oute-mind/
├── src/estimator/
│   ├── config/
│   │   ├── agents.yaml          # 6 agent definitions (role, goal, backstory)
│   │   └── tasks.yaml           # 6 task definitions (description, expected_output)
│   ├── tools/
│   │   ├── postgres_tool.py     # GetChecklist, SearchHistory, SearchPatterns, Save*
│   │   ├── jina_reader_tool.py  # Cloud web reader (r.jina.ai)
│   │   └── mindsdb_tool.py      # StoreContext, RetrieveContext
│   ├── crew.py                  # Pipeline orchestration (6 agents, sequential)
│   ├── api.py                   # FastAPI endpoints (9 routes)
│   ├── dashboard.html           # Health check UI
│   └── main.py                  # CLI entrypoint
├── configs/
│   ├── Caddyfile                # Reverse proxy routes
│   ├── postgres-init.sql        # Schema: 4 tables + indexes + triggers
│   └── prometheus.yml           # Metrics scrape targets
├── app/Dockerfile               # Python 3.13-slim + uv
├── docker-compose.yml           # 8 services + 3 oute-main services
└── reference/
    ├── DEEPWIKI.md              # Technical deep dive
    ├── architecture.excalidraw.md # Diagrams for Excalidraw
    └── implementation_plan.md   # Roadmap
```

---

## Troubleshooting

| Problem                    | Fix                                                       |
|----------------------------|------------------------------------------------------------|
| OPENAI_API_KEY error       | Set any `sk-proj-...` value in `.env.production`           |
| Gemini 404                 | Check `MODEL` env var — use `google/gemini-2.5-flash-lite` |
| CrewAI google-genai error  | Ensure `crewai[google-genai]` extra in pyproject.toml      |
| QdrantConfig missing       | Set `QDRANT_URL` and `QDRANT_API_KEY` env vars             |
| Out of memory              | `docker stats` — need 16GB minimum                         |
| 504 timeout                | Check Gemini API rate limits or increase Caddy timeout     |

---

**Maintained by**: Renato Bardi
**License**: Private
