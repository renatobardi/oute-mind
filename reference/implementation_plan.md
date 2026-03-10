# 🏗️ Plano de Implementação - Estimator MVP1 (POC)

Este documento detalha as etapas técnicas para transformar o planejamento atual em um sistema funcional rodando em uma VM dedicada.

## 🚀 Fase 1: Infraestrutura (The Foundation)
**Objetivo**: Preparar a VM para receber a stack.

- [ ] **Configurar Docker & Docker Compose**: Instalar drivers e preparar o ambiente de contêineres.
- [ ] **Provisionar Banco de Dados**:
    - [ ] Deploy do PostgreSQL (Configurar esquemas para checklists e JSONB para patterns).
    - [ ] Deploy do Qdrant (Configurar coleções para Team, User e Estimation).
- [ ] **Instalar Intelligence Layer**:
    - [ ] Deploy do MindsDB para orquestração de memória.
    - [ ] Configurar Redis para a fila de mensageria da Crew.

## 🤖 Fase 2: Realização dos Agentes (The Crew)
**Objetivo**: Implementar as ferramentas e a lógica de decisão.

- [ ] **Desenvolvimento de Ferramentas Customizadas**:
    - [ ] `PostgresTool`: Leitura de checklists e escrita de resultados.
    - [ ] `JinaReaderTool`: Wrapper para chamadas ao `r.jina.ai`.
    - [ ] `MindsDBTool`: Sincronismo de contexto entre agentes.
- [ ] **Refinamento de Prompts**: Ajustar as instruções nos YAMLs para garantir que o Gemini 1.5 extraia o máximo das mídias (áudio/vídeo).

## 🔌 Fase 3: API & Orquestração (The Interface)
**Objetivo**: Expor a Crew para o frontend.

- [ ] **Criar API FastAPI**:
    - [ ] Endpoint `/run`: Inicia a estimativa e retorna o ID.
    - [ ] Endpoint `/approve`: Recebe a aprovação humana do fluxo 1 para o 2.
    - [ ] Endpoint `/status`: Consulta o progresso através do Redis.
- [ ] **Implementar Processamento Assíncrono**: Integrar Celery ou RQ (Redis Queue) para gerenciar o ciclo de vida da Crew.

## 🏁 Fase 4: Validação & POC
**Objetivo**: Testar o fluxo de ponta a ponta.

- [ ] **Teste Multi-modal**: Subir um vídeo de arquitetura e validar se o Agente 1 entende o escopo.
- [ ] **Ciclo de Aprovação**: Testar a pausa e retomada entre o fluxo 1 e 2.
- [ ] **Relatório Final**: Validar se o Agente 3 persiste os dados corretamente para os templates (PDF/Excel).

---
*Este plano será atualizado conforme o progresso da implementação.*
