# 🎯 Estimator - Software Project Estimator with RAG

Uma CrewAI avançada projetada para realizar orçamentos e especificações técnicas de projetos de software, utilizando **PostgreSQL (JSONB)**, **Jina.ai** e **RAG Multi-tenant** para máxima precisão.

## 🚀 Visão Geral
O **Estimator** automatiza o ciclo de vida da estimativa de software: desde a descoberta multi-modal (áudio, vídeo, imagem) até a modelagem financeira de cenários com IA vs. Humanos.

---

## 🏗️ Estrutura do Projeto
```text
oute-mind/
├── src/estimator/       # 📦 Núcleo da Inteligência (CrewAI)
│   ├── config/          # ⚙️ Definições YAML de Comportamento e Tarefas
│   ├── tools/           # 🛠️ Ferramentas Customizadas (Postgres, Jina, AIMind)
│   ├── crew.py          # 🤖 Orquestração da Crew (Pipeline de 6 Agentes)
│   └── main.py          # 🚀 Ponto de Entrada (FastAPI & CLI)
├── reference/           # 📖 DEEPWIKI & Plano de Implementação
└── knowledge/           # 📚 Base RAG Multi-tenant (PDFs, Docs, History)
```

---

## 👥 Agentes de Elite (Workflow POC)

1.  **Solution Architect (Interviewer)**: Descoberta multi-modal via checklists PostgreSQL. Capta contexto de áudio/vídeo.
2.  **Technical Analyst (RAG)**: Navega em silos de conhecimento via **Qdrant** e faz pesquisas vivas com **Jina.ai**.
3.  **Software Architect (Designer)**: Consolida achados em arquitetura formal e persiste no banco de dados.
4.  **Cost Specialist (FinOps)**: Compara custos de desenvolvimento Humano vs. IA vs. Híbrido.
5.  **Reviewer & Presenter**: Facilita o aceite do cliente com feedback loop estruturado.
6.  **Knowledge Specialist**: *(Paralelo)* Expande a memória do sistema para o próximo projeto.

---

## ⚡ Diferenciais Tecnológicos

*   **Gemini 2.0 Flash**: Motor de inteligência multi-modal nativo para análise de mídias ricas.
*   **PostgreSQL + JSONB**: Abordagem híbrida para dados relacionais e flexibilidade de padrões NoSQL.
*   **RAG Multi-tenant**: Isolamento lógico de conhecimento por Time, Usuário e Projeto.
*   **Jina.ai Integration**: Leitura otimizada de documentação web para eliminar alucinações técnicas.

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
