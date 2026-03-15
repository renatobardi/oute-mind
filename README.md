# oute-mind

Sistema multi-agente de estimativa de projetos de software. Recebe uma descrição de projeto e produz um relatório completo com três cenários de custo (humano, IA, híbrido), análise de risco e recomendações de arquitetura. Parte do ecossistema oute — compartilha infraestrutura de banco de dados e rede com o `oute-main`.

[![Deploy to GCP](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml/badge.svg)](https://github.com/renatobardi/oute-mind/actions/workflows/deploy-to-gcp.yml)

---

## Serviços

| Serviço          | Container            | Porta interna | Descrição                              |
|------------------|----------------------|---------------|----------------------------------------|
| FastAPI           | `oute-app`          | 8000          | API REST + pipeline de agentes         |
| PostgreSQL        | `oute-postgres`     | 5432          | Checklists, histórico, padrões         |
| Redis             | `oute-redis`        | 6379          | Estado de jobs assíncronos             |
| Qdrant            | `oute-qdrant`       | 6333          | Vector DB para RAG                     |
| MindsDB           | `oute-mindsdb`      | 47334         | Contexto compartilhado entre agentes   |
| Caddy             | `oute-caddy`        | 80 / 443      | Reverse proxy + TLS automático         |
| Prometheus        | `oute-prometheus`   | 9090          | Coleta de métricas (interno)           |
| Grafana           | `oute-grafana`      | 3000          | Dashboards de monitoramento (interno)  |
| Dashboard (main)  | `oute-dashboard`    | 3000          | SvelteKit — `/dashboard`              |
| Auth (main)       | `oute-auth-profile` | 3001          | Auth API — `/api/auth`                |
| Projects (main)   | `oute-projects`     | 3002          | Projects API — `/api/projects`        |
| Interview (main)  | `oute-interview`    | 3002          | Chat UI — `/chat`                     |
| Home (main)       | `oute-home`         | 3003          | Landing page — `/`                    |
| Oops (main)       | `oute-oops`         | 3004          | Página de erro fallback               |

> Todos os serviços usam `expose` (sem binding de porta no host). Caddy é o único ponto de entrada externo.

---

## Desenvolvimento local

```bash
git clone https://github.com/renatobardi/oute-mind.git
cd oute-mind

# Configurar variáveis de ambiente
cp .env.production.example .env.production
# Editar .env.production com suas API keys

# Subir todos os serviços
docker compose up -d

# Verificar saúde
curl http://localhost/health
```

> **Dependência**: `oute-main` deve estar clonado em `../oute-main` (mesmo nível que `oute-mind`), pois o `docker-compose.yml` faz build dos pacotes de lá.

```bash
# Testar o pipeline de estimativa
curl -X POST http://localhost/run \
  -H "Content-Type: application/json" \
  -d '{"project_details": "E-commerce com React e FastAPI"}'

# Verificar status
curl http://localhost/status/{estimation_id}
```

---

## Stack tecnológica

| Camada           | Tecnologia                        | Versão          |
|------------------|-----------------------------------|-----------------|
| Orquestração     | CrewAI                            | 1.10.1          |
| LLM              | Gemini 2.5 Flash-Lite (Google)    | via `google/gemini-2.5-flash-lite` |
| Linguagem        | Python                            | >=3.10, <3.14   |
| API              | FastAPI + Uvicorn                 | >=0.104.0       |
| Banco de dados   | PostgreSQL                        | 16-alpine       |
| Vector DB        | Qdrant                            | latest          |
| Cache / Queue    | Redis                             | 7-alpine        |
| Memória agentes  | MindsDB                           | latest          |
| Web reader       | Jina Reader                       | cloud (r.jina.ai) |
| Busca web        | Serper                            | cloud (google.serper.dev) |
| Proxy reverso    | Caddy                             | latest          |
| Monitoramento    | Prometheus + Grafana              | latest          |
| Infra            | GCP Compute Engine (ARM64)        | t2a-standard-4  |

---

## CI/CD

Push para `main` dispara deploy automático via GitHub Actions (`.github/workflows/deploy-to-gcp.yml`):

```
push → main → autenticação WIF → SSH via gcloud → git pull (oute-mind + oute-main) → docker compose build → docker compose up -d → health check
```

Autenticação sem chaves SSH — usa Workload Identity Federation (WIF) do GCP.

Deploy manual de emergência:

```bash
gcloud compute ssh oute-mind --zone=us-central1-a \
  --command="sudo -u renatobardicabral_gmail_com bash -c '
    cd ~/oute-mind && git pull origin main
    cd ~/oute-main && git pull origin main
    cd ~/oute-mind && docker compose build && docker compose up -d
  '"
```

---

## Documentação

| Arquivo                              | Conteúdo                                      |
|--------------------------------------|-----------------------------------------------|
| `docs/DEPLOYMENT_GCP.md`            | Setup completo de infraestrutura GCP          |
| `docs/reference/DEEPWIKI.md`        | Deep dive técnico do sistema                  |
| `docs/reference/architecture.excalidraw.md` | Diagramas de arquitetura (Excalidraw) |
| `docs/reference/implementation_plan.md`     | Roadmap de implementação              |
| `docs/adr/`                         | Architecture Decision Records                 |

---

**Maintained by**: Renato Bardi
**License**: Private
