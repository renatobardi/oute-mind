## 🏗️ Sobre o Estimator

O **Estimator** é um sistema de multi-agentes (CrewAI) especializado em gerar orçamentos e especificações técnicas de alta fidelidade para projetos de software. Ele utiliza **RAG Multi-tenant** no Qdrant e processamento **Multi-modal** nativo do Gemini 1.5 Flash para entender requisitos vindo de textos, áudios, imagens e vídeos.

---

## 👥 Agentes do Sistema

O projeto conta com 6 agentes especializados configurados em `src/estimator/config/agents.yaml`:
1.  **Solution Architect (Interviewer)**: Descoberta e checklists relacional.
2.  **Technical Analyst (RAG)**: Pesquisa histórica e validação web (Jina.ai).
3.  **Software Architect (Designer)**: Design técnico e persistência Postgres.
4.  **Cost Specialist (FinOps)**: Cenários financeiros e otimização.
5.  **Reviewer & Presenter**: Revisão funcional e loop de aceite.
6.  **Knowledge Specialist**: Memória de longo prazo (Paralelo).

---

## 🚀 Como Executar

O projeto utiliza `uv` para gestão de dependências.

1.  **Instalação**:
    ```bash
    uv sync
    ```
2.  **Configuração**: Adicione suas chaves no `.env` (GEMINI_API_KEY, SERPER_API_KEY, etc).
3.  **Execução**:
    ```bash
    uv run estimator run
    ```

## Support

For support, questions, or feedback regarding the SoftwareProjectEstimatorWithRag Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
