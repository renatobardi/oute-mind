# oute-mind Architecture — Excalidraw Import

> Copy each section into Excalidraw as text elements and arrange visually.
> Use the shapes reference table at the bottom for consistent styling.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                          GCP VM · t2a-standard-4                            │
│                          ARM64 · 16GB RAM · 4 vCPU                          │
│                          Ubuntu 22.04 · us-central1-a                       │
│                                                                             │
│   ┌──────────────┐         ┌────────────────────────────────────────────┐   │
│   │              │         │            FastAPI + CrewAI                │   │
│   │    Caddy     │────────▶│            oute-app :8000                 │   │
│   │    :80       │         │                                            │   │
│   │              │         │   ┌────────────────────────────────────┐   │   │
│   └──────────────┘         │   │     CrewAI Sequential Pipeline    │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 1 ──▶ [Approval Gate]     │   │   │
│                            │   │                    │               │   │   │
│                            │   │              Agent 2 ──▶ Agent 3  │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 3 ──▶ Agent 4 ──▶ Agent 5 │   │   │
│                            │   │                                    │   │   │
│                            │   │   Agent 5 ──▶ Agent 6              │   │   │
│                            │   └────────────────────────────────────┘   │   │
│                            └───────────┬──────┬──────┬──────┬──────────┘   │
│                                        │      │      │      │              │
│                    ┌───────────────┐    │      │      │      │              │
│                    │ PostgreSQL 16 │◀───┘      │      │      │              │
│                    │ (JSONB)       │           │      │      │              │
│                    │ :5432         │           │      │      │              │
│                    └───────────────┘           │      │      │              │
│                                               │      │      │              │
│                    ┌───────────────┐           │      │      │              │
│                    │ Redis 7       │◀──────────┘      │      │              │
│                    │ (job state)   │                  │      │              │
│                    │ :6379         │                  │      │              │
│                    └───────────────┘                  │      │              │
│                                                      │      │              │
│                    ┌───────────────┐                  │      │              │
│                    │ Qdrant        │◀─────────────────┘      │              │
│                    │ (vectors)     │                         │              │
│                    │ :6333         │                         │              │
│                    └───────────────┘                         │              │
│                                                             │              │
│                    ┌───────────────┐                         │              │
│                    │ MindsDB       │◀────────────────────────┘              │
│                    │ (context)     │                                        │
│                    │ :47334        │                                        │
│                    └───────────────┘                                        │
│                                                                             │
│   ┌───────────────┐    ┌───────────────┐                                   │
│   │  Prometheus   │───▶│   Grafana     │                                   │
│   │  :9090        │    │   :3080       │                                   │
│   └───────────────┘    └───────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
            External APIs     │ (outbound only)
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
  │  AGENT 1                        │
  │  software_architecture_         │
  │  interviewer                    │
  │  ─────────────────────────────  │
  │  Role: Solution Architect       │
  │  Multi-modal discovery          │
  │                                 │
  │  Tools:                         │
  │  · FileReadTool                 │
  │  · OCRTool                      │
  │  · ScrapeWebsiteTool            │
  │  · GetChecklistTool        [PG] │
  │  · SaveEstimationTool      [PG] │
  │  · StoreContextTool        [MB] │
  │                                 │
  │  Output: discovery_findings     │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │     CLIENT APPROVAL GATE       │
  │     human_input=True            │
  │     POST /approve/{id}          │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 2                        │
  │  technical_research_analyst_    │
  │  with_rag                       │
  │  ─────────────────────────────  │
  │  Role: Technical Analyst        │
  │  RAG search + web validation    │
  │                                 │
  │  Tools:                         │
  │  · QdrantVectorSearchTool  [QD] │
  │  · SerperDevTool                │
  │  · JinaReaderTool          [JN] │
  │  · SearchEstimationHistory [PG] │
  │  · SearchPatternsTool      [PG] │
  │  · RetrieveContextTool     [MB] │
  │                                 │
  │  Output: research_findings      │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 3                        │
  │  software_architect             │
  │  ─────────────────────────────  │
  │  Role: Designer & Consolidator  │
  │  Architecture + persist         │
  │                                 │
  │  Tools:                         │
  │  · QdrantVectorSearchTool  [QD] │
  │  · SearchPatternsTool      [PG] │
  │  · SaveEstimationTool      [PG] │
  │  · StoreContextTool        [MB] │
  │  · RetrieveContextTool     [MB] │
  │                                 │
  │  Output: design_blueprint       │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 4                        │
  │  cost_optimization_specialist   │
  │  ─────────────────────────────  │
  │  Role: FinOps Specialist        │
  │  3 financial scenarios          │
  │                                 │
  │  Scenarios:                     │
  │  A) human-only                  │
  │  B) ai-only                     │
  │  C) hybrid                      │
  │                                 │
  │  Tools:                         │
  │  · ScrapeWebsiteTool            │
  │  · SaveFinancialScenarioTool[PG]│
  │  · RetrieveContextTool     [MB] │
  │                                 │
  │  Output: financial_scenarios    │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 5                        │
  │  reviewer_and_presenter         │
  │  ─────────────────────────────  │
  │  Role: Tech-Functional Reviewer │
  │  Cross-validation + summary     │
  │  human_input=True               │
  │                                 │
  │  Tools:                         │
  │  · QdrantVectorSearchTool  [QD] │
  │  · SerperDevTool                │
  │  · SearchEstimationHistory [PG] │
  │  · RetrieveContextTool     [MB] │
  │                                 │
  │  Output: final_report           │
  └──────────────┬──────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────┐
  │  AGENT 6                        │
  │  knowledge_management_          │
  │  specialist                     │
  │  ─────────────────────────────  │
  │  Role: Knowledge Guardian       │
  │  Index into Qdrant for RAG      │
  │                                 │
  │  Tools:                         │
  │  · QdrantVectorSearchTool  [QD] │
  │  · SaveEstimationTool      [PG] │
  │  · StoreContextTool        [MB] │
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

  Legend:
  [PG] = PostgreSQL   [QD] = Qdrant
  [MB] = MindsDB      [JN] = Jina Reader (cloud)
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
                   │  Redis   │     │  Tools                   │
                   │ (state)  │     │                          │
                   │          │     │  postgres_tool.py ──────▶ PostgreSQL
                   │ key:     │     │    GetChecklistTool             │
                   │ job:{id} │     │    SearchEstimationHistoryTool  │
                   │          │     │    SearchPatternsTool           │
                   │ fields:  │     │    SaveEstimationTool           │
                   │  status  │     │    SaveFinancialScenarioTool    │
                   │  phase   │     │                          │
                   │  result  │     │  jina_reader_tool.py ──▶ r.jina.ai
                   │          │     │    JinaReaderTool               │
                   │ TTL: 24h │     │                          │
                   └──────────┘     │  mindsdb_tool.py ──────▶ MindsDB
                                    │    StoreContextTool             │
                                    │    RetrieveContextTool          │
                                    │                          │
                                    │  crewai built-in:        │
                                    │    QdrantVectorSearch ──▶ Qdrant
                                    │    SerperDevTool ───────▶ Serper
                                    │    FileReadTool          │
                                    │    OCRTool               │
                                    │    ScrapeWebsiteTool     │
                                    └──────────────────────────┘
```

---

## 4. Database Schema

```
  PostgreSQL · estimator schema
  ─────────────────────────────

  ┌──────────────────────────────┐
  │  estimator.checklists        │
  │  ────────────────────────    │
  │  id          UUID (PK)       │
  │  project_id  UUID             │
  │  phase       VARCHAR(50)      │
  │    'initial_scoping'          │
  │    'technical_deep_dive'      │
  │    'integration_review'       │
  │  content     JSONB            │
  │  created_at  TIMESTAMP        │
  │  updated_at  TIMESTAMP (trig) │
  └──────────────────────────────┘

  ┌──────────────────────────────┐
  │  estimator.estimation_history│
  │  ────────────────────────    │
  │  id          UUID (PK)       │
  │  project_id  UUID             │
  │  team_id     UUID             │
  │  user_id     UUID             │
  │  phase       INT (1-6)        │
  │  status      VARCHAR(50)      │
  │    'completed'                │
  │    'in_progress'              │
  │    'approved'                 │
  │    'pending_approval'         │
  │  data        JSONB            │
  │  created_at  TIMESTAMP        │
  │  updated_at  TIMESTAMP (trig) │
  └──────────────────────────────┘

  ┌──────────────────────────────┐
  │  estimator.patterns          │
  │  ────────────────────────    │
  │  id           UUID (PK)      │
  │  pattern_name VARCHAR(255) UQ│
  │  description  TEXT            │
  │  pattern_data JSONB           │
  │  created_at   TIMESTAMP       │
  │  updated_at   TIMESTAMP (trig)│
  └──────────────────────────────┘

  ┌──────────────────────────────┐
  │  estimator.financial_scenarios│
  │  ────────────────────────    │
  │  id             UUID (PK)    │
  │  estimation_id  UUID          │
  │  scenario_type  VARCHAR(50)   │
  │    'human-only'               │
  │    'ai-only'                  │
  │    'hybrid'                   │
  │  costs          JSONB         │
  │  timeline       JSONB         │
  │  risks          JSONB         │
  │  created_at     TIMESTAMP     │
  └──────────────────────────────┘

  Indexes:
  · idx_checklists_project_id
  · idx_estimation_history_project_id
  · idx_estimation_history_team_id
  · idx_patterns_name
  · idx_financial_scenarios_estimation_id

  Extensions: uuid-ossp, pg_trgm


  Qdrant · Vector Collections
  ───────────────────────────

  ┌───────────────────────────┐
  │  knowledge_base           │
  │  (default collection)     │
  │  Configurable via env:    │
  │  QDRANT_COLLECTION        │
  └───────────────────────────┘


  MindsDB · Agent Context
  ───────────────────────

  ┌───────────────────────────┐
  │  agent_context (table)    │
  │  ─────────────────────    │
  │  key_name     VARCHAR     │
  │  agent_name   VARCHAR     │
  │  context_data JSON        │
  │  created_at   TIMESTAMP   │
  │                           │
  │  Keys used:               │
  │  · discovery_findings     │
  │  · design_blueprint       │
  │  · knowledge_enrichment   │
  │  · rag_validation         │
  └───────────────────────────┘


  Redis · Job State
  ─────────────────

  ┌───────────────────────────┐
  │  key: job:{estimation_id} │
  │  TTL: 86400 (24h)         │
  │  ─────────────────────    │
  │  status        string     │
  │  current_phase int        │
  │  phase_name    string     │
  │  started_at    ISO 8601   │
  │  completed_at  ISO 8601   │
  │  result        string     │
  │  error         string     │
  └───────────────────────────┘
```

---

## 5. Network & Ports

```
  Internet
     │
     │ :80 (HTTP)
     ▼
  ┌──────────┐
  │  Caddy   │──── /dashboard*  ────▶ :3000 (oute-dashboard)
  │          │──── /api/auth*   ────▶ :3001 (oute-auth)
  │          │──── /api/projects* ──▶ :3002 (oute-projects)
  │          │──── /* (default) ────▶ :8000 (FastAPI)
  └──────────┘

  Internal Network (oute-network, bridge)
  ────────────────────────────────────────
  oute-app :8000     ──▶  oute-postgres   :5432
  oute-app :8000     ──▶  oute-redis      :6379
  oute-app :8000     ──▶  oute-qdrant     :6333
  oute-app :8000     ──▶  oute-mindsdb    :47334
  oute-prometheus    ──▶  oute-app        :8000 (scrape /metrics)
  oute-grafana       ──▶  oute-prometheus :9090

  External (outbound only, no containers)
  ────────────────────────────────────────
  oute-app ──▶ generativelanguage.googleapis.com (Gemini 2.5 Flash-Lite)
  oute-app ──▶ r.jina.ai (Jina Reader cloud API)
  oute-app ──▶ google.serper.dev (Serper web search)
```

---

## 6. CI/CD Pipeline

```
  Developer
     │
     │  git push origin main
     ▼
  ┌──────────────────────────────────────┐
  │   GitHub Actions                     │
  │   deploy-to-gcp.yml                  │
  │                                      │
  │   1. Checkout code                   │
  │   2. Configure SSH (Ed25519)         │
  │   3. Create .env from GH Secrets     │
  │   4. SCP all files to VM             │
  │   5. SSH → docker compose down       │
  │   6. SSH → docker compose build      │
  │   7. SSH → docker compose up -d      │
  │   8. Sleep 30s (health check wait)   │
  │   9. SSH → curl /health              │
  │  10. Get VM IP from GCP              │
  │  11. Verify deployment               │
  └──────────────┬───────────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────────┐
  │   GCP VM: oute-mind                  │
  │   us-central1-a                      │
  │   Static IP: oute-mind-ip            │
  │                                      │
  │   Accessible at:                     │
  │   http://<IP>/healthcheck            │
  │   http://<IP>:3080 (Grafana)         │
  │   http://<IP>:9090 (Prometheus)      │
  └──────────────────────────────────────┘
```

---

## 7. Tool Map (all 13 tools)

```
  ┌──────────────────────────────────────────────────────────────┐
  │                    TOOL INVENTORY                            │
  │                                                              │
  │  Custom Tools (src/estimator/tools/)                         │
  │  ──────────────────────────────────                          │
  │                                                              │
  │  postgres_tool.py:                                           │
  │  ├─ GetChecklistTool          → estimator.checklists         │
  │  ├─ SearchEstimationHistoryTool → estimator.estimation_history│
  │  ├─ SearchPatternsTool        → estimator.patterns           │
  │  ├─ SaveEstimationTool        → estimator.estimation_history │
  │  └─ SaveFinancialScenarioTool → estimator.financial_scenarios│
  │                                                              │
  │  jina_reader_tool.py:                                        │
  │  └─ JinaReaderTool            → https://r.jina.ai/{url}     │
  │                                                              │
  │  mindsdb_tool.py:                                            │
  │  ├─ StoreContextTool          → mindsdb:47334 SQL API       │
  │  └─ RetrieveContextTool       → mindsdb:47334 SQL API       │
  │                                                              │
  │                                                              │
  │  CrewAI Built-in Tools (crewai_tools)                        │
  │  ──────────────────────────────────                          │
  │  ├─ FileReadTool              → local filesystem             │
  │  ├─ OCRTool                   → image/PDF text extraction    │
  │  ├─ ScrapeWebsiteTool         → HTTP scraping                │
  │  ├─ QdrantVectorSearchTool    → qdrant:6333 (knowledge_base) │
  │  └─ SerperDevTool             → google.serper.dev            │
  │                                                              │
  │  Total: 8 custom + 5 built-in = 13 tools                    │
  └──────────────────────────────────────────────────────────────┘
```

---

## Shapes Reference for Excalidraw

| Element           | Shape              | Color         | Border    |
|-------------------|--------------------|---------------|-----------|
| Client/User       | Cloud              | `#E8E8E8`     | `#888888` |
| FastAPI/App       | Rectangle (bold)   | `#4A90D9`     | `#2C5F8A` |
| Agents (1-6)      | Rounded rectangle  | `#7B68EE`     | `#5B48CE` |
| PostgreSQL        | Cylinder           | `#336791`     | `#1A4C6E` |
| Redis             | Cylinder           | `#DC382D`     | `#A01A10` |
| Qdrant            | Cylinder           | `#24B47E`     | `#0D8A5C` |
| MindsDB           | Cylinder           | `#00B4D8`     | `#007B94` |
| External APIs     | Diamond            | `#FFB347`     | `#CC8A2E` |
| Approval Gate     | Diamond            | `#FF6B6B`     | `#CC4444` |
| Network boundary  | Dashed rectangle   | transparent   | `#888888` |
| Data flow arrows  | Arrow              | `#333333`     | —         |
| Monitoring        | Rectangle          | `#DDA0DD`     | `#AA70AA` |
| GCP VM boundary   | Rectangle (dashed) | transparent   | `#4285F4` |
