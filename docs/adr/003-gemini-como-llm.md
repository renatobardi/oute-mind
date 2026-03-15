# ADR 003 — Gemini 2.5 Flash-Lite como LLM principal

**Status**: aceito
**Data**: 2026-03

## Contexto

O sistema precisa de um LLM capaz de raciocínio multi-modal (texto, imagens, documentos, áudio) para a fase de descoberta de requisitos (Agent 1). O modelo também precisa ter boa relação custo/performance para 6 chamadas por estimativa.

## Decisão

Usar `google/gemini-2.5-flash-lite` via LiteLLM (integração nativa do CrewAI). Todos os 6 agentes usam o mesmo modelo.

## Razões

- **Multi-modal**: Gemini Flash suporta imagens, PDFs e áudio nativamente — necessário para o Agent 1 processar inputs variados do cliente.
- **Custo**: Flash-Lite é a variante mais econômica da família Gemini 2.5, adequada para o volume atual.
- **LiteLLM**: o CrewAI abstrai a chamada via LiteLLM, permitindo trocar de modelo sem alterar código — apenas a env var `MODEL`.
- **OPENAI_API_KEY**: LiteLLM requer a variável mesmo sem usar OpenAI. Valor fictício (`sk-proj-*`) é suficiente.

## Consequências

- Dependência de disponibilidade da API do Google (sem fallback configurado).
- Rate limits do Gemini podem causar timeout de 504 em picos de uso.
- Trocar de modelo é trivial: alterar `MODEL` no `.env.production`.
