# Security Backlog

Itens de seguranca pendentes para implementar quando o MVP estiver estavel.

## Concluido

- [x] **Etapa 1** — Remover portas expostas no host (docker-compose `ports` → `expose`)
- [x] **Etapa 3** — Firewall GCP: remover regras desnecessarias (mindsdb, rdp, ssh aberto)
- [x] **Etapa 3** — Firewall GCP: adicionar regra HTTPS (443)

## Backlog

### Etapa 2 — HTTPS com Caddy (quando tiver dominio)

- [ ] Configurar dominio apontando para 34.132.93.171
- [ ] Atualizar Caddyfile para usar dominio (Let's Encrypt automatico)
- [ ] Redirect HTTP (80) → HTTPS (443)

### Etapa 5 — Hardening de containers

Adicionar no `docker-compose.yml` para cada servico:

- [ ] `security_opt: [no-new-privileges:true]` — impede escalacao de privilegios
- [ ] `read_only: true` — filesystem somente leitura
- [ ] `tmpfs: [/tmp, /run]` — pastas temporarias necessarias
- [ ] `mem_limit` — limitar memoria por container para evitar consumo total

Servicos para aplicar:
- [ ] postgres
- [ ] redis
- [ ] qdrant
- [ ] mindsdb
- [ ] app (FastAPI)
- [ ] prometheus
- [ ] grafana
- [ ] 00_dashboard
- [ ] 01_auth-profile
- [ ] 02_projects
- [ ] caddy

> Testar cada servico individualmente pois `read_only` pode quebrar servicos que gravam em disco.
