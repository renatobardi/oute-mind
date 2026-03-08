# 🎯 Estimator - Software Project Estimator with RAG

Uma CrewAI avançada projetada para realizar orçamentos e especificações técnicas de projetos de software, utilizando **PostgreSQL (JSONB)**, **Jina.ai** e **RAG Multi-tenant** para máxima precisão.

## 🚀 Visão Geral
O **Estimator** automatiza o ciclo de vida da estimativa de software: desde a descoberta multi-modal (áudio, vídeo, imagem) até a modelagem financeira de cenários com IA vs. Humanos.

---

## 🏗️ Estrutura do Projeto

```text
oute-mind/
├── src/estimator/       # 📦 Pacote principal
│   ├── config/          # ⚙️ Definições de Agentes e Tarefas (YAML)
│   ├── crew.py          # 🤖 Orquestração da Crew (6 Agentes)
│   └── main.py          # 🚀 Ponto de entrada (CLI)
├── knowledge/           # 📚 Base de conhecimento (Multi-tenant)
├── reference/           # 📖 DEEPWIKI, Plano de Implantação e Docs
└── AGENTS.md            # 📝 Referência vital para assistentes de IA
```

---

## 👥 Fluxo de Trabalho (Pipeline 1-6)

1.  **Solution Architect (Interviewer)**: Descoberta multi-modal via checklists Postgres. 
    *   *(Ponto de Aprovação Humana obrigatório)*
2.  **Technical Analyst (RAG Specialist)**: Validação histórica via Postgres (JSONB) e Jina.ai Reader.
3.  **Software Architect (Designer)**: Design técnico/funcional e persistência para relatórios.
4.  **Cost Specialist (FinOps)**: Modelagem de 3 resultados (Somente Humano, Somente IA, Híbrido).
5.  **Reviewer & Presenter**: Revisão final, feedback loop e aceite pelo cliente.
6.  **Knowledge Specialist**: *(Paralelo)* Enriquecimento da base vetorial Qdrant.

---

## 📈 Deployment & POC
O projeto está configurado para um deploy **Self-hosted em VM dedicada** via Docker Compose, utilizando o Google Gemini 2.0 Flash como motor de inteligência externo.

Consulte o [Plano de Implementação](file:///Users/bardi/Projetos/oute-mind/reference/implementation_plan.md) para detalhes de setup.

---

## 🏃 Como Executar

```bash
uv run estimator run
```

---

> [!IMPORTANT]
> O fluxo entre a etapa 1 e a etapa 2 exige aprovação manual do cliente para garantir o alinhamento do escopo.
