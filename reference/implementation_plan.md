# 🏗️ Plano de Implementação - Estimator MVP1 (POC)

Este documento detalha as etapas técnicas para transformar o planejamento atual em um sistema funcional rodando em uma VM dedicada.

---

## ✅ Fase 1: Infraestrutura (The Foundation) — CONCLUÍDA

- [x] **Configurar Docker & Docker Compose**: Stack completa em `docker-compose.yml` (9 serviços)
- [x] **Provisionar Banco de Dados**:
    - [x] Deploy do PostgreSQL 16 (schema `estimator` com 4 tabelas JSONB em `configs/postgres-init.sql`)
    - [x] Deploy do Qdrant (configurado no docker-compose)
- [x] **Instalar Intelligence Layer**:
    - [x] Deploy do MindsDB para orquestração de memória
    - [x] Configurar Redis para fila de mensageria e estado de jobs
- [x] **Reverse Proxy**: Caddy configurado com security headers
- [x] **Monitoramento base**: Prometheus + Grafana no docker-compose

## ✅ Fase 2: Realização dos Agentes (The Crew) — CONCLUÍDA

- [x] **Desenvolvimento de Ferramentas Customizadas**:
    - [x] `PostgresTool`: 5 tools (GetChecklist, SearchHistory, SearchPatterns, SaveEstimation, SaveFinancialScenario)
    - [x] `JinaReaderTool`: Wrapper para Jina Reader local (retorna markdown limpo)
    - [x] `MindsDBTool`: StoreContext e RetrieveContext para sincronismo entre agentes
- [x] **Refinamento de Prompts**: Agentes e tasks com instruções step-by-step referenciando tools por nome

## ✅ Fase 3: API & Orquestração (The Interface) — CONCLUÍDA

- [x] **Criar API FastAPI**:
    - [x] Endpoint `POST /run`: Inicia estimativa assíncrona, retorna ID
    - [x] Endpoint `POST /approve/{id}`: Aprovação humana entre fase 1 e 2
    - [x] Endpoint `GET /status/{id}`: Consulta progresso via Redis
    - [x] Endpoint `POST /estimate`: Execução síncrona (legacy)
- [x] **Processamento Assíncrono**: Background threads com estado em Redis (TTL 24h)
- [x] **`run_with_trigger`**: Entrypoint para iniciar FastAPI server

## ✅ Fase 4: Deploy GCP — CONCLUÍDA

- [x] **Provisionar VM GCP**: Comandos gcloud prontos (`t2a-standard-4`, 4vCPU, 16GB, IP estático)
- [x] **GitHub Secrets**: Template completo em `DEPLOYMENT_GCP.md` (API keys, DB passwords, SSH)
- [x] **GitHub Actions CI/CD**: Workflow `deploy-to-gcp.yml` (build → SSH deploy → health check)
- [x] **Firewall GCP**: Regras para HTTP/80 e SSH/22 com IP whitelist
- [x] **Reverse Proxy + HTTPS**: Caddy configurado (HTTP/IP para POC, pronto para Let's Encrypt com domínio)

---

## 🔜 Fase 5: Hardening & Observabilidade (Fase 2 do Produto)

### Dados & Inicialização
- [ ] Criar tabela `agent_context` no MindsDB para sincronismo entre agentes
- [ ] Popular checklists iniciais no PostgreSQL (initial_scoping, technical_deep_dive, integration_review)
- [ ] Criar coleções no Qdrant (project_patterns, technical_patterns, cost_history, knowledge_base)

### Pipeline Assíncrono
- [ ] Implementar approval gate real no worker (pausar após fase 1, aguardar POST /approve)
- [ ] Atualizar fase no Redis durante execução (fases 2→3→4→5 intermediárias)
- [ ] Validar entrypoint do Dockerfile com `run_with_trigger`

### Monitoramento
- [ ] Configurar Prometheus targets apontando para a app FastAPI
- [ ] Criar dashboard Grafana (latência, success rate, uso de memória)
- [ ] Instrumentar FastAPI com prometheus-client (métricas por endpoint e por agente)

### Validação & Testes
- [ ] Teste multi-modal: vídeo/áudio de arquitetura → Agente 1
- [ ] Teste do ciclo de aprovação end-to-end (pausa/retomada)
- [ ] Teste de persistência Postgres → templates de relatório (PDF/Excel)
- [ ] Validar Docker build com todas as novas dependências

---
*Última atualização: 2026-03-10 — Fases 1-4 concluídas, Fase 5 planejada.*
