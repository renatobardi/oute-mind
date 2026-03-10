import os
from dotenv import load_dotenv

# Load environment variables (try .env.production first, then .env)
_env_path = "/app/.env.production" if os.path.exists("/app/.env.production") else ".env"
load_dotenv(_env_path, override=True)

# Explicitly ensure OPENAI_API_KEY is set from file before importing CrewAI
# Required for LiteLLM provider initialization (key won't be used for actual requests)
if "OPENAI_API_KEY" not in os.environ or not os.environ.get("OPENAI_API_KEY"):
    try:
        with open(_env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    key_value = line.strip().split('=', 1)[1] if '=' in line else None
                    if key_value:
                        os.environ['OPENAI_API_KEY'] = key_value
                        break
    except Exception as e:
        print(f"Warning: Could not read OPENAI_API_KEY from {_env_path}: {e}")

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Get model from environment or default
DEFAULT_MODEL = os.getenv("MODEL", "google/gemini-2.5-flash-lite")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
from crewai_tools import (
	FileReadTool,
	OCRTool,
	ScrapeWebsiteTool,
	QdrantVectorSearchTool,
	SerperDevTool
)
from crewai_tools.tools.qdrant_vector_search_tool.qdrant_search_tool import QdrantConfig

# Qdrant configuration from environment
QDRANT_CONFIG = QdrantConfig(
    qdrant_url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
    qdrant_api_key=os.getenv("QDRANT_API_KEY"),
    collection_name=os.getenv("QDRANT_COLLECTION", "knowledge_base"),
)
from estimator.tools import (
	GetChecklistTool,
	SearchEstimationHistoryTool,
	SearchPatternsTool,
	SaveEstimationTool,
	SaveFinancialScenarioTool,
	JinaReaderTool,
	StoreContextTool,
	RetrieveContextTool,
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
                ScrapeWebsiteTool(),
                GetChecklistTool(),
                SaveEstimationTool(),
                StoreContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
        )

    @agent
    def technical_research_analyst_with_rag(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_research_analyst_with_rag"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(qdrant_config=QDRANT_CONFIG),
                SerperDevTool(),
                JinaReaderTool(),
                SearchEstimationHistoryTool(),
                SearchPatternsTool(),
                RetrieveContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
        )

    @agent
    def software_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["software_architect"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(qdrant_config=QDRANT_CONFIG),
                SearchPatternsTool(),
                SaveEstimationTool(),
                StoreContextTool(),
                RetrieveContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
        )

    @agent
    def cost_optimization_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["cost_optimization_specialist"], # type: ignore[index]
            tools=[
                ScrapeWebsiteTool(),
                SaveFinancialScenarioTool(),
                RetrieveContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
        )

    @agent
    def reviewer_and_presenter(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer_and_presenter"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(qdrant_config=QDRANT_CONFIG),
                SerperDevTool(),
                SearchEstimationHistoryTool(),
                RetrieveContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
        )

    @agent
    def knowledge_management_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["knowledge_management_specialist"], # type: ignore[index]
            tools=[
                QdrantVectorSearchTool(qdrant_config=QDRANT_CONFIG),
                SaveEstimationTool(),
                StoreContextTool(),
            ],
            verbose=True,
            llm=LLM(model=DEFAULT_MODEL, temperature=LLM_TEMPERATURE),
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
            chat_llm=LLM(model=DEFAULT_MODEL),
        )
