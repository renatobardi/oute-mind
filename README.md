# 🎯 Estimator - Software Project Estimator with RAG

Uma CrewAI avançada projetada para realizar orçamentos e especificações técnicas de projetos de software, utilizando **PostgreSQL (JSONB)**, **Jina.ai** e **RAG Multi-tenant** para máxima precisão.

## 🚀 Visão Geral
O **Estimator** automatiza o ciclo de vida da estimativa de software: desde a descoberta multi-modal (áudio, vídeo, imagem) até a modelagem financeira de cenários com IA vs. Humanos.

---

## 🏗️ Estrutura do Projeto
```text
oute-mind/
├── src/estimator/       # 📦 Núcleo da Inteligência (CrewAI)
│   ├── config/          # ⚙️ Definições YAML de Comportamento e Tarefas
│   ├── tools/           # 🛠️ Ferramentas Customizadas (Postgres, Jina, AIMind)
│   ├── crew.py          # 🤖 Orquestração da Crew (Pipeline de 6 Agentes)
│   └── main.py          # 🚀 Ponto de Entrada (FastAPI & CLI)
├── reference/           # 📖 DEEPWIKI & Plano de Implementação
└── knowledge/           # 📚 Base RAG Multi-tenant (PDFs, Docs, History)
```

---

## 👥 Agentes de Elite (Workflow POC)

1.  **Solution Architect (Interviewer)**: Descoberta multi-modal via checklists PostgreSQL. Capta contexto de áudio/vídeo.
2.  **Technical Analyst (RAG)**: Navega em silos de conhecimento via **Qdrant** e faz pesquisas vivas com **Jina.ai**.
3.  **Software Architect (Designer)**: Consolida achados em arquitetura formal e persiste no banco de dados.
4.  **Cost Specialist (FinOps)**: Compara custos de desenvolvimento Humano vs. IA vs. Híbrido.
5.  **Reviewer & Presenter**: Facilita o aceite do cliente com feedback loop estruturado.
6.  **Knowledge Specialist**: *(Paralelo)* Expande a memória do sistema para o próximo projeto.

---

## ⚡ Diferenciais Tecnológicos

*   **Gemini 2.0 Flash**: Motor de inteligência multi-modal nativo para análise de mídias ricas.
*   **PostgreSQL + JSONB**: Abordagem híbrida para dados relacionais e flexibilidade de padrões NoSQL.
*   **RAG Multi-tenant**: Isolamento lógico de conhecimento por Time, Usuário e Projeto.
*   **Jina.ai Integration**: Leitura otimizada de documentação web para eliminar alucinações técnicas.

---

## 📈 Deployment & POC
O projeto está configurado para um deploy **Self-hosted em VM dedicada** via Docker Compose, utilizando o Google Gemini 1.5 Flash como motor de inteligência externo.

---

## 🚀 Quick Start

### Pré-requisitos
- Docker & Docker Compose (v2+)
- Python 3.13+
- API Keys:
  - `GOOGLE_API_KEY` (Google Gemini)
  - `SERPER_API_KEY` (Busca web)
  - `COMPOSIO_API_KEY` (Integrações)
  - `OCR_API_KEY` (Processamento de docs)

### Desenvolvimento Local

```bash
# Clonar repositório
git clone https://github.com/renatobardi/oute-mind.git
cd oute-mind

# Configurar ambiente
cp .env.production.example .env.production
# Editar .env.production com suas API keys

# Instalar dependências
uv pip install -r pyproject.toml

# Iniciar serviços (PostgreSQL, Redis, Qdrant, MindsDB)
docker-compose up -d

# Executar estimação
uv run estimator run_with_trigger
```

### Via Docker Compose (Produção)

```bash
# Construir e iniciar stack completo
docker-compose up -d

# Verificar saúde
curl http://localhost:8000/health

# Fazer requisição de estimação
curl -X POST http://localhost:8000/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "estimation_id": "proj-001",
    "project_details": "Construir plataforma SaaS com React + FastAPI..."
  }'
```

---

## 🔌 API Endpoints

### Health Check
```
GET /health
```
Resposta: `{"status": "healthy", "service": "software-estimator"}`

### API Status
```
GET /api/status
```
Resposta: Status completo + estado da crew

### Executar Estimação
```
POST /estimate
Content-Type: application/json

{
  "estimation_id": "proj-001",
  "project_details": "Descrição completa do projeto..."
}
```

Resposta:
```json
{
  "estimation_id": "proj-001",
  "result": "Estimação detalhada com 3 cenários...",
  "status": "success"
}
```

---

## ⚙️ Variáveis de Ambiente

### API Keys Obrigatórias
```bash
GOOGLE_API_KEY=sk-xxxxx              # Google Gemini API
SERPER_API_KEY=xxxxx                 # Busca web Serper
COMPOSIO_API_KEY=xxxxx               # Composio integration
OCR_API_KEY=xxxxx                    # OCR para documentos
OPENAI_API_KEY=xxxxx                 # Obrigatório pelo CrewAI (não usado)
```

### Bancos de Dados
```bash
POSTGRES_USER=oute_prod_user
POSTGRES_PASSWORD=xxxxx              # Auto-gerado, 32 chars
POSTGRES_DB=oute_production

REDIS_PASSWORD=xxxxx                 # Auto-gerado, 32 chars

QDRANT_API_KEY=xxxxx                 # Auto-gerado, 32 chars
QDRANT_MASTER_KEY=xxxxx              # Auto-gerado, 32 chars
QDRANT_URL=http://qdrant:6333

MINDSDB_ADMIN_USER=mindsdb
MINDSDB_ADMIN_PASSWORD=xxxxx         # Auto-gerado, 32 chars
MINDS_API_KEY=local-mindsdb-not-used # SDK compatibility
```

### Aplicação
```bash
MODEL=google/gemini-1.5-flash        # Modelo LLM a usar
LLM_TEMPERATURE=0.7                  # Nível de criatividade
FASTAPI_PORT=8000                    # Porta da API
FASTAPI_WORKERS=4                    # Processos Uvicorn
```

---

## 🚀 Deployment em GCP (Recomendado)

```bash
# 1. Configurar variáveis
export PROJECT_ID="oute-mind"
export GCP_ZONE="us-central1-a"
export VM_NAME="oute-mind"
export MY_PUBLIC_IP="SEU.IP.AQUI"

# 2. Criar infraestrutura GCP
gcloud compute instances create ${VM_NAME} \
  --machine-type=t2a-standard-4 \
  --image-family=ubuntu-2204-lts \
  --zone=${GCP_ZONE}

# 3. Configurar firewall
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80,tcp:443 --source-ranges=0.0.0.0/0

# 4. SSH e deploy
gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE}
# Na VM:
docker-compose up -d

# 5. Acessar aplicação
curl http://<IP_DA_VM>:8000/health
```

**Custo Estimado**: ~R$ 500/mês (t2a-standard-4 ARM, 16GB RAM, 4 vCPU)

Ver [DEPLOYMENT_GCP.md](./DEPLOYMENT_GCP.md) para instruções detalhadas.

---

## 🐛 Troubleshooting

### Status dos Containers

```bash
# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f app         # FastAPI
docker-compose logs -f postgres    # Banco de dados
docker-compose logs -f mindsdb     # MindsDB
```

### Erros de Conexão

```bash
# Aumentar timeout no docker-compose.yml
# Reiniciar containers
docker-compose restart
```

### Erros de Permissão no Banco

```bash
# Verificar credenciais
cat .env.production

# Reiniciar PostgreSQL e app
docker-compose restart postgres app
```

### Memória Insuficiente (OOM)

```bash
# Verificar uso
docker stats

# Aumentar memória do Docker
# (Settings > Resources no Docker Desktop)
```

---

## 📊 Monitoramento

### Dashboards
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **FastAPI Docs**: http://localhost:8000/docs

### Métricas Importantes
- Tempo de execução de agentes
- Latência de respostas da API
- Performance de queries
- Uso de CPU/Memória
- Performance de busca vetorial

---

## 🔐 Segurança

- **Secrets**: Use GitHub Secrets em produção
- **SSH Keys**: Ed25519 para acesso à VM GCP
- **Firewall**: Restrito às portas necessárias (22, 80, 443)
- **Banco de dados**: Senhas auto-geradas de 32 caracteres
- **API Keys**: Nunca fazer commit (em .gitignore)

---

## 📚 Referências

- **CrewAI**: https://docs.crewai.com
- **Google Gemini**: https://ai.google.dev
- **FastAPI**: https://fastapi.tiangolo.com
- **Docker Compose**: https://docs.docker.com/compose
- **GCP**: https://cloud.google.com/compute

Consulte o [Plano de Implementação](./reference/implementation_plan.md) e [DeepWiki](./reference/DEEPWIKI.md) para detalhes técnicos.

---

## 🏃 Como Executar

```bash
uv run estimator run
```

---

> [!IMPORTANT]
> O fluxo entre a etapa 1 e a etapa 2 exige aprovação manual do cliente para garantir o alinhamento do escopo.
