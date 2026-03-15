# Project Overview

> oute-mind is a CrewAI multi-agent system that generates software project estimations with three cost scenarios (human-only, ai-only, hybrid).

## How it works

1. Client sends a project description via `POST /run`
2. Six AI agents process the request sequentially (90-130 seconds)
3. Client approves scope after Agent 1 via `POST /approve/{id}`
4. System returns a complete estimation with costs, risks, and architecture

## Agents

| #  | Code Name                                 | Role                 | What it does                                               |
|----|-------------------------------------------|----------------------|------------------------------------------------------------|
| 1  | `software_architecture_interviewer`       | Solution Architect   | Multi-modal discovery (text, audio, video, images)         |
| 2  | `technical_research_analyst_with_rag`     | Technical Analyst    | RAG validation + web research (Jina Reader, Serper)        |
| 3  | `software_architect`                      | Designer             | Consolidates into formal architecture design               |
| 4  | `cost_optimization_specialist`            | FinOps               | Three scenarios: human-only / ai-only / hybrid             |
| 5  | `reviewer_and_presenter`                  | Reviewer             | Cross-validation + client-facing summary                   |
| 6  | `knowledge_management_specialist`         | Knowledge Guardian   | Indexes results into Qdrant for future estimations         |

Agents 1 and 5 have `human_input=True` (approval gates).

## Custom Tools (8 total)

| Tool Class                    | Backend    | File                |
|-------------------------------|------------|---------------------|
| `GetChecklistTool`            | PostgreSQL | `postgres_tool.py`  |
| `SearchEstimationHistoryTool` | PostgreSQL | `postgres_tool.py`  |
| `SearchPatternsTool`          | PostgreSQL | `postgres_tool.py`  |
| `SaveEstimationTool`          | PostgreSQL | `postgres_tool.py`  |
| `SaveFinancialScenarioTool`   | PostgreSQL | `postgres_tool.py`  |
| `JinaReaderTool`              | r.jina.ai  | `jina_reader_tool.py` |
| `StoreContextTool`            | MindsDB    | `mindsdb_tool.py`   |
| `RetrieveContextTool`         | MindsDB    | `mindsdb_tool.py`   |

Plus 5 built-in CrewAI tools: FileReadTool, OCRTool, ScrapeWebsiteTool, QdrantVectorSearchTool, SerperDevTool.

## Stack

- **LLM**: Google Gemini 2.5 Flash-Lite (via LiteLLM, configurable via `MODEL` env var)
- **Orchestration**: CrewAI v1.10.1 (sequential process)
- **Database**: PostgreSQL 16 (JSONB) — 4 tables in `estimator` schema
- **Vector DB**: Qdrant — `knowledge_base` collection
- **Cache**: Redis 7 — async job state (key: `job:{id}`, TTL 24h)
- **Memory**: MindsDB — `agent_context` table for inter-agent sync
- **Web Reader**: Jina Reader cloud API (r.jina.ai, no container)
- **API**: FastAPI + Uvicorn (9 endpoints)
- **Proxy**: Caddy (:80)
- **Monitoring**: Prometheus (:9090) + Grafana (:3080)
- **Infra**: GCP Compute Engine (t2a-standard-4, ARM64, 16GB)

## Key Files

```
src/estimator/crew.py            # 6 agents, 6 tasks, sequential pipeline
src/estimator/api.py             # 9 FastAPI endpoints
src/estimator/config/agents.yaml # Agent role, goal, backstory
src/estimator/config/tasks.yaml  # Task description, expected_output
src/estimator/tools/             # 8 custom tools (Postgres, Jina, MindsDB)
src/estimator/dashboard.html     # Health check visual UI
configs/postgres-init.sql        # 4 tables + indexes + triggers
docker-compose.yml               # 8 core + 3 oute-main services
```
