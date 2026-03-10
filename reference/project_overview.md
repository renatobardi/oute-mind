# Project Overview

> oute-mind is a CrewAI multi-agent system that generates software project estimations with three cost scenarios (human, AI, hybrid).

## How it works

1. Client sends a project description via `POST /run`
2. Six AI agents process the request sequentially (90-130 seconds)
3. System returns a complete estimation with costs, risks, and architecture

## Agents

| #  | Agent                | What it does                                               |
|----|----------------------|------------------------------------------------------------|
| 1  | Solution Architect   | Multi-modal discovery (text, audio, video, images)         |
| 2  | Technical Analyst    | RAG validation + web research (Jina Reader, Serper)        |
| 3  | Software Architect   | Consolidates into formal architecture design               |
| 4  | Cost Specialist      | Three financial scenarios: human / AI / hybrid             |
| 5  | Reviewer             | Cross-validation + client-facing summary                   |
| 6  | Knowledge Manager    | Indexes results into Qdrant for future estimations         |

## Stack

- **LLM**: Google Gemini 2.5 Flash-Lite (via LiteLLM)
- **Orchestration**: CrewAI v1.10.1
- **Database**: PostgreSQL 16 (JSONB) — estimations, patterns, history
- **Vector DB**: Qdrant — RAG semantic search
- **Cache**: Redis 7 — async job state
- **Memory**: MindsDB — agent context sync
- **Web Reader**: Jina Reader cloud API (r.jina.ai)
- **API**: FastAPI + Uvicorn
- **Proxy**: Caddy (HTTP/HTTPS)
- **Infra**: GCP Compute Engine (t2a-standard-4, ARM64, 16GB)

## Key Files

```
src/estimator/crew.py            # Agent pipeline definition
src/estimator/api.py             # FastAPI endpoints
src/estimator/config/agents.yaml # Agent prompts and config
src/estimator/config/tasks.yaml  # Task definitions
src/estimator/tools/             # Custom tools (Postgres, Jina, MindsDB)
docker-compose.yml               # Full stack definition
```
