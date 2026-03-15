# ADR 004 — Qdrant como vector database para RAG

**Status**: aceito
**Data**: 2026-03

## Contexto

O pipeline usa RAG (Retrieval-Augmented Generation) para enriquecer as estimativas com padrões históricos e documentação técnica. É necessário um vector store para busca semântica.

## Decisão

Usar Qdrant rodando como container Docker (`qdrant/qdrant:latest`), com a collection `knowledge_base`.

## Razões

- **Integração nativa com CrewAI**: `crewai_tools` inclui `QdrantVectorSearchTool` com suporte a `QdrantConfig` — zero boilerplate.
- **Self-hosted**: roda no mesmo Docker Compose, sem custo de serviço gerenciado.
- **Performance**: Qdrant é escrito em Rust, baixo overhead de memória comparado a alternativas como Weaviate ou Pinecone self-hosted.

## Consequências

- Dados de vector persistidos em `volumes/qdrant/` — backup manual necessário.
- Sem replicação ou alta disponibilidade na configuração atual.
- `QDRANT_API_KEY` protege o endpoint interno.
