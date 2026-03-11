#!/bin/bash
set -e

echo "🚀 Setup Inicial - oute-mind no GCP"

# Update system
echo "📦 Atualizando sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
echo "🐳 Instalando Docker..."
sudo apt-get install -y docker.io docker-compose curl wget git jq
sudo usermod -aG docker ${USER}
newgrp docker

# Create directory structure
echo "📂 Criando diretórios..."
mkdir -p ~/oute-mind/{configs,volumes/{postgres,qdrant,redis,mindsdb,prometheus,grafana,caddy},logs}

# Clone repository
echo "📥 Clonando repositório..."
cd ~/oute-mind
git clone https://github.com/renatobardi/oute-mind.git . 2>/dev/null || git pull

# Create .env from template
if [ ! -f ~/.env.production ]; then
    echo "⚙️  Criando .env.production..."
    cp .env.production.example .env.production
    echo "⚠️  Edite .env.production com suas credenciais antes de executar docker-compose!"
fi

echo "✅ Setup completo!"
echo ""
echo "Próximos passos:"
echo "1. Configure os secrets no GitHub (Settings > Secrets and variables > Actions)"
echo "2. Edite .env.production com suas credenciais"
echo "3. Execute: docker-compose pull && docker-compose up -d"
echo "4. Verifique: docker-compose ps"
