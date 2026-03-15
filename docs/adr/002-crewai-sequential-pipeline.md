# ADR 002 — CrewAI com pipeline sequencial de 6 agentes

**Status**: aceito
**Data**: 2026-03

## Contexto

O processo de estimativa de projetos de software requer etapas com dependência de dados: o arquiteto precisa do output da descoberta, o especialista de custo precisa do output do arquiteto, e assim por diante. O sistema precisa orquestrar múltiplos agentes de IA com ferramentas distintas e passar contexto entre eles.

## Decisão

Usar CrewAI (`crewai==1.10.1`) com `Process.sequential` — 6 agentes rodam em ordem fixa, o output de cada um alimenta o próximo.

## Razões

- **Dependência de dados**: o pipeline é inerentemente sequencial. Paralelismo não agrega valor aqui.
- **CrewAI**: oferece abstração de agente+tarefa+ferramenta com YAML config, `human_input`, e integração nativa com Qdrant, Serper, Jina.
- **human_input=True**: permite pausar o pipeline para aprovação humana entre Agent 1 (descoberta) e Agent 2 (pesquisa), e novamente no Agent 5 (revisão final) — necessário para o fluxo de negócio.
- **YAML config**: separação entre definição de agente (`agents.yaml`) e lógica de orquestração (`crew.py`) facilita ajuste de prompts sem tocar código.

## Consequências

- Tempo de execução: 90–130s por estimativa (limitado por latência do Gemini, não por CPU).
- Sem retry automático por agente — falha em qualquer step aborta o pipeline.
- `human_input=True` requer que o cliente esteja presente durante a execução (não é fire-and-forget puro).
