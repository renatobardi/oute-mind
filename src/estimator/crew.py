import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	FileReadTool,
	OCRTool,
	AIMindTool,
	ScrapeWebsiteTool,
	ComposioTool,
	QdrantVectorSearchTool,
	SerperDevTool
)

@CrewBase
class SoftwareProjectEstimatorWithRagCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # --- Agents ---

    @agent
    def software_architecture_interviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["software_architecture_interviewer"], # type: ignore[index]
            tools=[
                FileReadTool(), 
                OCRTool(), 
                ComposioTool(), 
                AIMindTool(), 
                ScrapeWebsiteTool()
            ],
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    @agent
    def technical_research_analyst_with_rag(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_research_analyst_with_rag"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(),
                SerperDevTool(), # Can be used with Jina r.jina.ai
                AIMindTool(),
                ScrapeWebsiteTool(), # Complementary to Jina
                # PostgresqlTool(), # Using JSONB for NoSQL patterns
            ],
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    @agent
    def software_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["software_architect"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(),
                AIMindTool(),
                # PostgresqlTool(), # To be implemented
            ],
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    @agent
    def cost_optimization_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["cost_optimization_specialist"], # type: ignore[index]
            tools=[ScrapeWebsiteTool()], # For GCP/AWS/Azure pricing
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    @agent
    def reviewer_and_presenter(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer_and_presenter"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(),
                SerperDevTool(),
                # PostgresqlTool(), # To be implemented
            ],
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    @agent
    def knowledge_management_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["knowledge_management_specialist"], # type: ignore[index]
            tools=[QdrantVectorSearchTool(), AIMindTool()],
            verbose=True,
            llm=LLM(model="google/gemini-2.0-flash", temperature=0.7),
        )

    # --- Tasks ---

    @task
    def conduct_architecture_discovery_session(self) -> Task:
        return Task(
            config=self.tasks_config["conduct_architecture_discovery_session"], # type: ignore[index]
            human_input=True
        )

    @task
    def rag_enhanced_technical_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["rag_enhanced_technical_analysis"], # type: ignore[index]
        )

    @task
    def consolidate_design_and_persist(self) -> Task:
        return Task(
            config=self.tasks_config["consolidate_design_and_persist"], # type: ignore[index]
        )

    @task
    def financial_scenario_modeling(self) -> Task:
        return Task(
            config=self.tasks_config["financial_scenario_modeling"], # type: ignore[index]
        )

    @task
    def final_review_and_presentation(self) -> Task:
        return Task(
            config=self.tasks_config["final_review_and_presentation"], # type: ignore[index]
            human_input=True 
        )

    @task
    def long_term_knowledge_enrichment(self) -> Task:
        return Task(
            config=self.tasks_config["long_term_knowledge_enrichment"], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SoftwareProjectEstimatorWithRag crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential, # Sequential execution for logic, enrichment as final step
            verbose=True,
            chat_llm=LLM(model="google/gemini-2.0-flash"),
        )
