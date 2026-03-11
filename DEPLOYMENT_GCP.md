# Deployment no Google Cloud Platform (GCP)

Este documento descreve como fazer o deployment da aplicação oute-mind no GCP.

## 📋 Pré-requisitos

- Conta GCP ativa
- Projeto GCP criado (ID: `oute-mind`)
- GitHub repository configurado
- Google Cloud SDK instalado localmente

## 🚀 Fase 1: Setup GCP (5-10 minutos)

### 1.1 Configure variáveis de ambiente

```bash
export PROJECT_ID="oute-mind"
export GCP_ZONE="us-central1-a"
export VM_NAME="oute-mind"
export MY_PUBLIC_IP="177.162.77.163"
```

### 1.2 Configure projeto GCP

```bash
gcloud config set project ${PROJECT_ID}
gcloud config set compute/zone ${GCP_ZONE}

# Habilitar APIs necessárias
gcloud services enable compute.googleapis.com
gcloud services enable cloudlogging.googleapis.com
gcloud services enable cloudmonitoring.googleapis.com
```

### 1.3 Criar a VM

```bash
gcloud compute instances create ${VM_NAME} \
  --machine-type=t2a-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --zone=${GCP_ZONE} \
  --metadata=enable-oslogin=TRUE \
  --tags=http-server,https-server,ssh-server \
  --scopes=compute-rw,storage-ro,logging-write,monitoring-write
```

### 1.4 Alocar IP estático

```bash
gcloud compute addresses create ${VM_NAME}-ip --region=us-central1

# Associar IP à VM
gcloud compute instances add-access-config ${VM_NAME} \
  --address=${VM_NAME}-ip \
  --zone=${GCP_ZONE}

# Obter IP (salve este valor!)
export VM_IP=$(gcloud compute addresses describe ${VM_NAME}-ip \
  --region=us-central1 --format="get(address)")

echo "IP alocado: $VM_IP"
```

### 1.5 Configurar Firewall

Only ports 22 (SSH), 80 (HTTP), 443 (HTTPS), and ICMP are allowed. All other ports (database, services, monitoring) are blocked externally. Services communicate internally via Docker network.

```bash
# HTTP
gcloud compute firewall-rules create allow-http-oute-mind \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server || echo "Regra pode já existir"

# HTTPS
gcloud compute firewall-rules create allow-https-oute-mind \
  --allow=tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=https-server || echo "Regra pode já existir"

# SSH (seu IP only)
gcloud compute firewall-rules create allow-ssh-oute-mind \
  --allow=tcp:22 \
  --source-ranges=${MY_PUBLIC_IP}/32 \
  --target-tags=ssh-server || echo "Regra pode já existir"

# ICMP (ping)
gcloud compute firewall-rules create allow-icmp-oute-mind \
  --allow=icmp \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server || echo "Regra pode já existir"
```

> **Security note**: Previous rules exposing MindsDB, RDP, and default SSH have been removed. No direct access to database ports (5432, 6379, 6333) or service ports (8000, 9090, 3080) is allowed from external networks.

## 🔧 Fase 2: Setup da VM (3-5 minutos)

### 2.1 Conectar via SSH

```bash
gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE}
```

### 2.2 Executar script de setup

Na VM:

```bash
# Fazer download do script
curl -O https://raw.githubusercontent.com/renatobardi/oute-mind/main/scripts/initial-setup.sh
chmod +x initial-setup.sh

# Executar
./initial-setup.sh
```

## 🔐 Fase 3: GitHub Secrets (5 minutos)

### 3.1 Gerar credenciais

Localmente:

```bash
bash scripts/generate-credentials.sh
```

### 3.2 Adicionar Secrets no GitHub

Vá em: `Settings > Secrets and variables > Actions`

Adicione os seguintes secrets:

```
# GCP
GCP_PROJECT_ID = "oute-mind"
GCP_VM_HOSTNAME = <seu IP da VM>
GCP_VM_USER = "ubuntu"
GCP_VM_SSH_PRIVATE_KEY = <sua chave SSH em base64>
GCP_VM_SSH_KNOWN_HOSTS = <será gerado ao conectar>
GCP_SERVICE_ACCOUNT_KEY = <sua service account em base64>

# API Keys
GOOGLE_API_KEY = <seu valor>
SERPER_API_KEY = <seu valor>
COMPOSIO_API_KEY = <seu valor>
OCR_API_KEY = <seu valor>

# Database
POSTGRES_USER = "oute_prod_user"
POSTGRES_PASSWORD = <gere com script acima>
QDRANT_API_KEY = <gere com script acima>

# Redis & MindsDB
REDIS_PASSWORD = <gere com script acima>
MINDSDB_ADMIN_PASSWORD = <gere com script acima>

# Grafana
GRAFANA_PASSWORD = <gere com script acima>
```

## 🐳 Fase 4: Deploy via GitHub Actions

### 4.1 Fazer push para main

```bash
git add .
git commit -m "Add GCP deployment configuration"
git push origin main
```

O workflow `deploy-to-gcp.yml` executará automaticamente.

### 4.2 Monitorar deploy

Vá em: `GitHub > Actions > Deploy to GCP`

Aguarde a conclusão. O IP da VM será exibido na saída.

## ✅ Validação

Após o deploy, teste:

```bash
# Substituir <IP> pelo IP da sua VM
curl http://<IP>/health
curl http://<IP>/api/status

# Acessar no navegador
http://<IP>            # Landing page (via Caddy)
http://<IP>/docs       # API Swagger UI (via Caddy)
```

> **Note**: Grafana, Prometheus, and Qdrant are internal-only (not exposed on host ports). Access via SSH tunnel:
> ```bash
> gcloud compute ssh oute-mind --zone=us-central1-a -- -L 3080:grafana:3000
> # Then open http://localhost:3080
> ```

## 📊 Acessar Serviços

| Serviço | Acesso | Notas |
|---------|--------|-------|
| FastAPI | `http://<IP>/health`, `http://<IP>/docs` | Via Caddy reverse proxy (port 80) |
| Grafana | Internal only | Access via SSH tunnel (`-L 3080:grafana:3000`) |
| Prometheus | Internal only | Access via SSH tunnel (`-L 9090:prometheus:9090`) |
| Qdrant | Internal only | Access via `docker exec` or SSH tunnel |

All services use `expose` (Docker internal network only). Only Caddy exposes ports 80 and 443 on the host.

## 🔍 Troubleshooting

### Conectar à VM para debug

```bash
gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE}

# Dentro da VM
docker compose ps                   # Ver status dos containers
docker compose logs -f app          # Ver logs da aplicação
docker compose logs -f caddy        # Ver logs do Caddy
```

### Obter IP novamente

```bash
gcloud compute addresses describe oute-mind-ip \
  --region=us-central1 --format="get(address)"
```

### Restartar containers

```bash
gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE} << 'EOF'
cd ~/oute-mind
docker compose restart
EOF
```

## 🧹 Limpeza

Para remover a VM e recursos (custo):

```bash
# Deletar VM
gcloud compute instances delete ${VM_NAME} --zone=${GCP_ZONE}

# Deletar IP estático
gcloud compute addresses delete ${VM_NAME}-ip --region=us-central1

# Deletar firewall rules
gcloud compute firewall-rules delete allow-http-oute-mind
gcloud compute firewall-rules delete allow-ssh-oute-mind
```

## 📚 Mais Informações

Veja `./reference/implementation_plan.md` para detalhes técnicos completos.
