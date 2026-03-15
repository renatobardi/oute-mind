# Deploy no GCP

O deploy é feito automaticamente via GitHub Actions ao fazer push para `main`.

---

## CI/CD (GitHub Actions)

Workflow: `.github/workflows/deploy-to-gcp.yml`

```
push → main → autenticação WIF → SSH via gcloud → git pull → docker compose build → docker compose up -d → health check
```

**Autenticação**: Workload Identity Federation (sem chaves de serviço).
- Pool: `github-pool`, Provider: `github-provider`
- Service account: `github-actions-deploy@oute-mind.iam.gserviceaccount.com`
- Deploy user (OS Login): `renatobardicabral_gmail_com`

**Secrets necessários no GitHub** (`Settings > Secrets and variables > Actions`):

```
# API Keys da aplicação
GOOGLE_API_KEY
SERPER_API_KEY
COMPOSIO_API_KEY
OCR_API_KEY
OPENAI_API_KEY

# Database
POSTGRES_USER
POSTGRES_PASSWORD
QDRANT_API_KEY

# Redis & MindsDB
REDIS_PASSWORD
MINDSDB_ADMIN_PASSWORD

# oute-main services
JWT_SECRET

# Grafana
GRAFANA_PASSWORD
```

> Nenhuma chave SSH privada é necessária — o acesso à VM usa OS Login via `gcloud compute ssh`.

---

## Infraestrutura GCP

| Recurso     | Spec                     |
|-------------|--------------------------|
| VM          | `oute-mind`              |
| Tipo        | t2a-standard-4 (ARM64)   |
| RAM         | 16 GB                    |
| Disco       | 50 GB SSD                |
| OS          | Ubuntu 22.04 LTS         |
| Região/Zona | us-central1-a            |
| IP estático | `oute-mind-ip`           |

---

## Setup inicial da VM (primeira vez)

### 1. Provisionar VM

```bash
export PROJECT_ID="oute-mind"
export GCP_ZONE="us-central1-a"
export VM_NAME="oute-mind"

gcloud config set project ${PROJECT_ID}

gcloud compute instances create ${VM_NAME} \
  --machine-type=t2a-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --zone=${GCP_ZONE} \
  --metadata=enable-oslogin=TRUE \
  --tags=http-server,https-server \
  --scopes=compute-rw,storage-ro,logging-write,monitoring-write
```

### 2. Alocar IP estático

```bash
gcloud compute addresses create ${VM_NAME}-ip --region=us-central1

gcloud compute instances add-access-config ${VM_NAME} \
  --address=${VM_NAME}-ip \
  --zone=${GCP_ZONE}

gcloud compute addresses describe ${VM_NAME}-ip \
  --region=us-central1 --format="get(address)"
```

### 3. Regras de firewall

```bash
gcloud compute firewall-rules create allow-http-oute-mind \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server || true
```

### 4. Conectar à VM e executar setup

```bash
gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE}
```

Na VM, executar `scripts/initial-setup.sh` do repositório.

### 5. Criar `.env.production` na VM

```bash
cp .env.production.example .env.production
# Editar com credenciais reais
```

---

## Deploy manual (emergência)

```bash
gcloud compute ssh oute-mind --zone=us-central1-a \
  --command="sudo -u renatobardicabral_gmail_com bash -c '
    cd ~/oute-mind && git pull origin main
    cd ~/oute-main && git pull origin main
    cd ~/oute-mind && ln -sf .env.production .env
    docker compose build && docker compose up -d
  '"
```

---

## Validação

```bash
# Health check
curl http://<IP>/health

# Status da API
curl http://<IP>/api/status

# Health visual (browser)
http://<IP>/healthcheck
```

---

## Troubleshooting

```bash
# Conectar à VM
gcloud compute ssh oute-mind --zone=us-central1-a

# Ver status dos containers
docker compose ps

# Ver logs da aplicação
docker compose logs --tail=50 app

# Ver logs do Caddy
docker compose logs --tail=50 caddy
```
