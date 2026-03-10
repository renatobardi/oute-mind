# Multi-arch build (AMD64 + ARM64)
FROM python:3.13-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copiar código
COPY . .

# Instalar dependências Python
RUN uv pip install --system -r pyproject.toml

# Add src to Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "--", "python", "-m", "estimator.api"]
