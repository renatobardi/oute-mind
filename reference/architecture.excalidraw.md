# oute-mind Architecture — Excalidraw Import

> Copy each section below into Excalidraw as text elements and arrange them visually.
> Use Excalidraw's "Paste as Markdown" or manually create the shapes based on the descriptions.

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                          GCP VM (t2a-standard-4)                            │
│                          ARM64 · 16GB · 4 vCPU                              │
│                                                                             │
│   ┌──────────────┐                                                          │
│   │              │         ┌────────────────────────────────────────────┐   │
│   │    Caddy     │────────▶│            FastAPI + CrewAI                │   │
│   │    :80       │         │            (oute-app :8000)                │   │
│   │              │         │                                            │   │
│   └──────────────┘         │   ┌────────────────────────────────────┐   │   │
│                            │   │        CrewAI Pipeline             │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 1 ──▶ Agent 2 ──▶ Agent 3 │   │   │
│                            │   │      │                             │   │   │
│                            │   │   [Approval]                       │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 3 ──▶ Agent 4 ──▶ Agent 5 │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 5 ──▶ Agent 6              │   │   │
│                            │   └────────────────────────────────────┘   │   │
│                            └───────────┬──────┬──────┬──────┬──────────┘   │
│                                        │      │      │      │              │
│                    ┌───────────────┐    │      │      │      │              │
│                    │               │◀───┘      │      │      │              │
│                    │  PostgreSQL   │           │      │      │              │
│                    │  16 (JSONB)   │           │      │      │              │
│                    │  :5432        │           │      │      │              │
│                    └───────────────┘           │      │      │              │
│                                               │      │      │              │
│                    ┌───────────────┐           │      │      │              │
│                    │               │◀──────────┘      │      │              │
│                    │    Redis      │                  │      │              │
│                    │  7-alpine     │                  │      │              │
│                    │  :6379        │                  │      │              │
│                    └───────────────┘                  │      │              │
│                                                      │      │              │
│                    ┌───────────────┐                  │      │              │
│                    │               │◀─────────────────┘      │              │
│                    │   Qdrant      │                         │              │
│                    │  (vector)     │                         │              │
│                    │  :6333        │                         │              │
│                    └───────────────┘                         │              │
│                                                             │              │
│                    ┌───────────────┐                         │              │
│                    │               │◀────────────────────────┘              │
│                    │   MindsDB     │                                        │
│                    │  :47334       │                                        │
│                    └───────────────┘                                        │
│                                                                             │
│   ┌───────────────┐    ┌───────────────┐                                   │
│   │  Prometheus   │───▶│   Grafana     │                                   │
│   │  :9090        │    │   :3080       │                                   │
│   └───────────────┘    └───────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
            External APIs     │
            ──────────────────┤
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
  │ Google       │  │  Jina Reader    │  │   Serper     │
  │ Gemini 2.5   │  │  r.jina.ai     │  │   (search)   │
  │ Flash-Lite   │  │  (cloud API)   │  │              │
  └──────────────┘  └─────────────────┘  └──────────────┘
```

---

## 2. Agent Pipeline Flow

```
  ┌─────────────────────────────────┐
  │          CLIENT REQUEST         │
  │     POST /run or /estimate      │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 1: Solution Architect    │
  │  ─────────────────────────────  │
  │  Multi-modal discovery          │
  │  Text · Audio · Video · Images  │
  │                                 │
  │  Tools:                         │
  │  FileRead, OCR, ScrapeWebsite   │
  │  GetChecklist, SaveEstimation   │
  │  StoreContext                   │
  │                                 │
  │  Output: discovery_findings     │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │     CLIENT APPROVAL GATE       │
  │     POST /approve/{id}          │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 2: Technical Analyst     │
  │  ─────────────────────────────  │
  │  RAG search + web validation    │
  │                                 │
  │  Tools:                         │
  │  Qdrant, Serper, JinaReader     │
  │  SearchHistory, SearchPatterns  │
  │  RetrieveContext                │
  │                                 │
  │  Output: research_findings      │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 3: Software Architect    │
  │  ─────────────────────────────  │
  │  Design consolidation           │
  │                                 │
  │  Tools:                         │
  │  Qdrant, SearchPatterns         │
  │  SaveEstimation, StoreContext   │
  │  RetrieveContext                │
  │                                 │
  │  Output: design_blueprint       │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 4: Cost Specialist       │
  │  ─────────────────────────────  │
  │  3 financial scenarios          │
  │                                 │
  │  Scenario A: Human-Only         │
  │  Scenario B: AI-Assisted        │
  │  Scenario C: Full AI            │
  │                                 │
  │  Tools:                         │
  │  ScrapeWebsite                  │
  │  SaveFinancialScenario          │
  │  RetrieveContext                │
  │                                 │
  │  Output: financial_scenarios    │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 5: Reviewer & Presenter  │
  │  ─────────────────────────────  │
  │  Cross-validation + summary     │
  │  Client-facing report           │
  │                                 │
  │  Tools:                         │
  │  Qdrant, Serper                 │
  │  SearchHistory, RetrieveContext │
  │                                 │
  │  Output: final_report           │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 6: Knowledge Manager     │
  │  ─────────────────────────────  │
  │  Index results into Qdrant      │
  │  for future RAG retrieval       │
  │                                 │
  │  Tools:                         │
  │  Qdrant, SaveEstimation         │
  │  StoreContext                   │
  │                                 │
  │  Output: knowledge_enrichment   │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │        ESTIMATION RESULT        │
  │   3 scenarios · risks · arch    │
  │   GET /status/{id}              │
  └─────────────────────────────────┘
```

---

## 3. Data Flow

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Client   │────▶│ FastAPI  │────▶│ CrewAI   │────▶│ Gemini   │
  │ (HTTP)   │     │ (api.py) │     │ (crew.py)│     │ 2.5 API  │
  └──────────┘     └────┬─────┘     └────┬─────┘     └──────────┘
                        │                │
                        │                │
                   ┌────▼─────┐     ┌────▼─────────────────────┐
                   │  Redis   │     │  Custom Tools            │
                   │ (state)  │     │                          │
                   │          │     │  postgres_tool.py ──────▶ PostgreSQL
                   │ job_id:  │     │  jina_reader_tool.py ──▶ r.jina.ai
                   │  status  │     │  mindsdb_tool.py ──────▶ MindsDB
                   │  result  │     │                          │
                   │  TTL:24h │     │  crewai_tools:           │
                   └──────────┘     │  QdrantVectorSearch ───▶ Qdrant
                                    │  SerperDevTool ────────▶ Serper
                                    │  FileReadTool            │
                                    │  OCRTool                 │
                                    │  ScrapeWebsiteTool       │
                                    └──────────────────────────┘
```

---

## 4. Database Schema

```
  PostgreSQL (estimator schema)
  ─────────────────────────────

  ┌─────────────────────────┐
  │  estimation_requests    │
  │  ─────────────────────  │
  │  id (PK)                │
  │  estimation_id (UNIQUE) │◀──────────────────────────────┐
  │  project_details        │                               │
  │  status                 │                               │
  │  created_at             │                               │
  └─────────────────────────┘                               │
                                                            │
  ┌─────────────────────────┐    ┌─────────────────────────┐│
  │  estimation_findings    │    │  estimation_costs       ││
  │  ─────────────────────  │    │  ─────────────────────  ││
  │  id (PK)                │    │  id (PK)                ││
  │  estimation_id (FK) ────│───▶│  estimation_id (FK) ────│┘
  │  agent_name             │    │  scenario_type          │
  │  findings (JSONB)       │    │  cost_breakdown (JSONB) │
  │  created_at             │    │  total_cost             │
  └─────────────────────────┘    │  timeline_weeks         │
                                 │  confidence_level       │
  ┌─────────────────────────┐    └─────────────────────────┘
  │  estimation_risks       │
  │  ─────────────────────  │
  │  id (PK)                │
  │  estimation_id (FK)     │
  │  risk_category          │
  │  description            │
  │  probability            │
  │  impact                 │
  │  mitigation             │
  └─────────────────────────┘


  Qdrant (vector collections)
  ───────────────────────────

  ┌───────────────────┐  ┌───────────────────┐
  │  knowledge_base   │  │ project_patterns  │
  │  (general docs)   │  │ (past projects)   │
  └───────────────────┘  └───────────────────┘

  ┌───────────────────┐  ┌───────────────────┐
  │technical_patterns │  │   cost_history    │
  │ (tech combos)     │  │ (past costs)      │
  └───────────────────┘  └───────────────────┘
```

---

## 5. Network & Ports

```
  Internet
     │
     │ :80 (HTTP)
     ▼
  ┌──────────┐
  │  Caddy   │──── reverse_proxy ────▶ :8000 (FastAPI)
  │          │──── /grafana* ────────▶ :3080 (Grafana)
  └──────────┘

  Internal Network (oute-network)
  ────────────────────────────────
  FastAPI :8000  ──▶  PostgreSQL :5432
  FastAPI :8000  ──▶  Redis      :6379
  FastAPI :8000  ──▶  Qdrant     :6333
  FastAPI :8000  ──▶  MindsDB    :47334
  Prometheus     ──▶  FastAPI    :8000 (scrape /metrics)
  Grafana        ──▶  Prometheus :9090

  External (outbound only)
  ────────────────────────
  FastAPI ──▶ generativelanguage.googleapis.com (Gemini)
  FastAPI ──▶ r.jina.ai (Jina Reader)
  FastAPI ──▶ google.serper.dev (Serper)
```

---

## 6. CI/CD Pipeline

```
  Developer
     │
     │  git push main
     ▼
  ┌──────────────────────┐
  │   GitHub Actions     │
  │   deploy-to-gcp.yml  │
  └──────────┬───────────┘
             │
             │  1. Checkout code
             │  2. Create .env from GitHub Secrets
             │  3. SCP files to VM
             │  4. SSH → docker compose build
             │  5. SSH → docker compose up -d
             │  6. curl /health (verify)
             │
             ▼
  ┌──────────────────────┐
  │   GCP VM             │
  │   oute-mind          │
  │   (production)       │
  └──────────────────────┘
```

---

## Shapes Reference for Excalidraw

When recreating in Excalidraw, use these shapes:

| Element           | Shape              | Color         |
|-------------------|--------------------|---------------|
| Client/User       | Cloud              | #E8E8E8       |
| FastAPI/App       | Rectangle (bold)   | #4A90D9       |
| Agents            | Rounded rectangle  | #7B68EE       |
| Databases         | Cylinder           | #50C878       |
| External APIs     | Diamond            | #FFB347       |
| Approval Gate     | Diamond (red)      | #FF6B6B       |
| Network boundary  | Dashed rectangle   | #888888       |
| Data flow         | Arrow              | #333333       |
| Monitoring        | Rectangle          | #DDA0DD       |
