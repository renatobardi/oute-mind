# API Reference — oute-mind

> Spec completa e interativa disponível em `/docs` (Swagger UI) quando o serviço está rodando.

Base URL (produção): `https://oute.pro`
Base URL (local): `http://localhost`

---

## Endpoints

| Método | Rota                       | Descrição                                         |
|--------|----------------------------|---------------------------------------------------|
| GET    | `/health`                  | Health check leve — retorna `{"status": "ok"}`    |
| GET    | `/health/services`         | Status de todos os 7 serviços backend             |
| GET    | `/healthcheck`             | Dashboard visual de saúde (HTML)                  |
| GET    | `/api/status`              | Versão da API + prontidão do crew                 |
| POST   | `/run`                     | Inicia estimativa assíncrona                      |
| GET    | `/status/{estimation_id}`  | Consulta progresso da estimativa                  |
| POST   | `/approve/{estimation_id}` | Aprova escopo descoberto (após Agent 1)            |
| POST   | `/estimate`                | Estimativa síncrona (bloqueante, 90–130s)         |
| GET    | `/docs`                    | Swagger UI (gerado pelo FastAPI)                  |

---

## Fluxo principal (assíncrono)

```
POST /run
  → { "estimation_id": "uuid" }

GET /status/{estimation_id}
  → { "status": "waiting_approval" }   # aguarda aprovação de escopo

POST /approve/{estimation_id}
  → { "status": "running" }

GET /status/{estimation_id}  (polling)
  → { "status": "completed", "result": { ... } }
```

## Payload de entrada — POST /run

```json
{
  "project_details": "Descrição do projeto em texto livre"
}
```

Também aceita URLs de documentos, imagens e áudio (processados pelo Agent 1 via FileRead/OCR).

## Payload de saída — resultado completo

```json
{
  "scenarios": {
    "human_only":  { "cost": ..., "timeline": ..., "risks": [...] },
    "ai_only":     { "cost": ..., "timeline": ..., "risks": [...] },
    "hybrid":      { "cost": ..., "timeline": ..., "risks": [...] }
  },
  "architecture": { ... },
  "checklist":    [ ... ]
}
```
