#!/bin/bash

# Script para gerar credenciais seguras para GitHub Secrets

echo "🔐 Gerando Credenciais Seguras para GitHub Secrets"
echo ""

echo "1️⃣  POSTGRES_PASSWORD (32 chars base64):"
POSTGRES_PASSWORD=$(openssl rand -base64 32)
echo "$POSTGRES_PASSWORD"
echo ""

echo "2️⃣  REDIS_PASSWORD (32 chars base64):"
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "$REDIS_PASSWORD"
echo ""

echo "3️⃣  QDRANT_API_KEY (32 chars hex):"
QDRANT_API_KEY=$(openssl rand -hex 16)
echo "$QDRANT_API_KEY"
echo ""

echo "4️⃣  QDRANT_MASTER_KEY (32 chars hex):"
QDRANT_MASTER_KEY=$(openssl rand -hex 16)
echo "$QDRANT_MASTER_KEY"
echo ""

echo "5️⃣  MINDSDB_ADMIN_PASSWORD (32 chars base64):"
MINDSDB_ADMIN_PASSWORD=$(openssl rand -base64 32)
echo "$MINDSDB_ADMIN_PASSWORD"
echo ""

echo "6️⃣  GRAFANA_PASSWORD (32 chars base64):"
GRAFANA_PASSWORD=$(openssl rand -base64 32)
echo "$GRAFANA_PASSWORD"
echo ""

echo "================================"
echo "📋 Copie os valores acima e adicione no GitHub:"
echo "   Settings > Secrets and variables > Actions"
echo ""
echo "Use estes nomes de secrets:"
echo "- POSTGRES_PASSWORD"
echo "- REDIS_PASSWORD"
echo "- QDRANT_API_KEY"
echo "- QDRANT_MASTER_KEY"
echo "- MINDSDB_ADMIN_PASSWORD"
echo "- GRAFANA_PASSWORD"
echo "================================"
