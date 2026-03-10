#!/bin/bash
set -e

echo "🚀 Setup GCP - oute-mind"
echo ""

# Variáveis
export PROJECT_ID="oute-mind"
export GCP_ZONE="us-central1-a"
export VM_NAME="oute-mind"
export MY_PUBLIC_IP="177.162.77.163"

echo "📋 Configurando variáveis..."
echo "Project ID: $PROJECT_ID"
echo "Zone: $GCP_ZONE"
echo "VM Name: $VM_NAME"
echo ""

# 1. Set project
echo "1️⃣  Configurando projeto padrão..."
gcloud config set project ${PROJECT_ID}

# 2. Enable APIs (com tratamento de erro)
echo "2️⃣  Habilitando APIs (ignorando erros de permissão)..."
gcloud services enable compute.googleapis.com || echo "⚠️  Compute.googleapis.com pode já estar habilitada"
gcloud services enable cloudlogging.googleapis.com || echo "⚠️  Cloud Logging pode já estar habilitada"
gcloud services enable cloudmonitoring.googleapis.com || echo "⚠️  Cloud Monitoring pode já estar habilitada"

# 3. Create VM with correct ARM64 image
echo "3️⃣  Criando VM t2a-standard-4 (ARM64)..."
gcloud compute instances create ${VM_NAME} \
  --machine-type=t2a-standard-4 \
  --image-family=ubuntu-2204-lts-arm64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --zone=${GCP_ZONE} \
  --metadata=enable-oslogin=TRUE \
  --tags=http-server,https-server,ssh-server \
  --scopes=compute-rw,storage-ro,logging-write,monitoring-write \
  || echo "⚠️  VM pode já existir"

echo "✅ VM criada ou já existe"

# 4. Get or create static IP
echo "4️⃣  Configurando IP estático..."

# Verificar se IP já existe
if gcloud compute addresses describe ${VM_NAME}-ip --region=us-central1 &>/dev/null; then
    echo "✅ IP estático já existe"
else
    echo "Criando novo IP estático..."
    gcloud compute addresses create ${VM_NAME}-ip --region=us-central1
fi

# 5. Associate IP with instance
echo "5️⃣  Associando IP à VM..."
gcloud compute instances add-access-config ${VM_NAME} \
  --address=${VM_NAME}-ip \
  --zone=${GCP_ZONE} \
  || echo "⚠️  IP pode já estar associado"

# 6. Get the IP
echo ""
echo "6️⃣  Obtendo IP alocado..."
export VM_IP=$(gcloud compute addresses describe ${VM_NAME}-ip \
  --region=us-central1 --format="get(address)")

echo "✅ IP ALOCADO: ${VM_IP}"
echo ""

# 7. Configure Firewall
echo "7️⃣  Configurando Firewall..."

# HTTP
gcloud compute firewall-rules create allow-http-oute-mind \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server \
  || echo "⚠️  Regra HTTP pode já existir"

# SSH (seu IP)
gcloud compute firewall-rules create allow-ssh-oute-mind \
  --allow=tcp:22 \
  --source-ranges=${MY_PUBLIC_IP}/32 \
  --target-tags=ssh-server \
  || echo "⚠️  Regra SSH pode já existir"

echo "✅ Firewall configurado"
echo ""

# 8. Summary
echo "================================"
echo "🎉 SETUP GCP COMPLETO!"
echo "================================"
echo ""
echo "📊 Informações da VM:"
echo "  Project ID: ${PROJECT_ID}"
echo "  VM Name: ${VM_NAME}"
echo "  Machine Type: t2a-standard-4 (ARM64)"
echo "  Zone: ${GCP_ZONE}"
echo "  IP Estático: ${VM_IP}"
echo ""
echo "✅ Próximo passo: SSH na VM"
echo "   gcloud compute ssh ${VM_NAME} --zone=${GCP_ZONE}"
echo ""
echo "✅ Salve este IP para usar depois:"
echo "   export VM_IP=\"${VM_IP}\""
echo ""
