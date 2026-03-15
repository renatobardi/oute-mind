# ADR 001 — GCP Compute Engine ARM64 como infraestrutura de deploy

**Status**: aceito
**Data**: 2026-03

## Contexto

O sistema roda um pipeline de 6 agentes de IA em sequência, cada um invocando o Gemini 2.5 Flash-Lite via API externa. O processo leva entre 90 e 130 segundos por estimativa. Além da API principal, sobem junto PostgreSQL, Redis, Qdrant, MindsDB, Prometheus, Grafana e os serviços do oute-main — total de ~14 containers.

## Decisão

Usar uma VM única `t2a-standard-4` (ARM64, 16 GB RAM) no GCP Compute Engine, região `us-central1-a`.

## Razões

- **Custo**: instâncias ARM64 (Tau T2A) são ~30% mais baratas que instâncias x86 equivalentes no GCP.
- **Workload fit**: o pipeline é CPU-bound apenas durante parsing de resposta; o gargalo real é latência de API externa (Gemini). ARM64 é suficiente.
- **Simplicidade**: VM única com Docker Compose elimina overhead de orquestração (Kubernetes, Cloud Run) para o estágio atual do produto.
- **Deploy via SSH**: GitHub Actions + Workload Identity Federation (WIF) faz SSH na VM e executa `docker compose up -d` — sem necessidade de registry de imagens ou pipeline de CI complexo.

## Consequências

- 16 GB RAM é o mínimo viável com todos os containers rodando simultaneamente.
- Deploy implica downtime breve (~10s) durante `docker compose up -d`.
- Não há auto-scaling — capacidade limitada a 1 estimativa concorrente por vez.
