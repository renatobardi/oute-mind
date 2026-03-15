"""PostgreSQL Tool for CrewAI agents.

Provides read/write access to the estimator schema:
- checklists: discovery checklists by phase
- estimation_history: historical estimation data (multi-tenant)
- patterns: reusable design/framework patterns (JSONB)
- financial_scenarios: cost scenario results
"""

import json
import os
from typing import Type

import psycopg2
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _get_connection():
    """Create a PostgreSQL connection from environment variables."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "oute_prod_user"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "oute_production"),
    )


# --- Checklist Tool (Agent 1: Interviewer) ---


class GetChecklistInput(BaseModel):
    """Input for fetching a discovery checklist."""

    phase: str = Field(
        ...,
        description="The discovery phase to fetch the checklist for, e.g. 'initial_scoping', 'technical_deep_dive', 'integration_review'.",
    )
    project_id: str | None = Field(
        default=None,
        description="Optional project UUID to filter checklists for a specific project.",
    )


class GetChecklistTool(BaseTool):
    name: str = "Get Discovery Checklist"
    description: str = (
        "Fetch a structured discovery checklist from PostgreSQL by phase. "
        "Use this to get interview questions and scoping checklists for client discovery sessions. "
        "Available phases: 'initial_scoping', 'technical_deep_dive', 'integration_review'."
    )
    args_schema: Type[BaseModel] = GetChecklistInput

    def _run(self, phase: str, project_id: str | None = None) -> str:
        try:
            conn = _get_connection()
            cur = conn.cursor()

            if project_id:
                cur.execute(
                    "SELECT id, phase, content FROM estimator.checklists WHERE phase = %s AND project_id = %s::uuid ORDER BY created_at",
                    (phase, project_id),
                )
            else:
                cur.execute(
                    "SELECT id, phase, content FROM estimator.checklists WHERE phase = %s ORDER BY created_at",
                    (phase,),
                )

            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                return f"No checklists found for phase '{phase}'."

            results = [{"id": str(row[0]), "phase": row[1], "content": row[2]} for row in rows]
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error fetching checklist: {e}"


# --- Estimation History Tool (Agent 2: Research Analyst) ---


class SearchHistoryInput(BaseModel):
    """Input for searching estimation history."""

    team_id: str | None = Field(
        default=None,
        description="Team UUID to filter estimations by team.",
    )
    project_id: str | None = Field(
        default=None,
        description="Project UUID to filter estimations by project.",
    )
    status: str | None = Field(
        default=None,
        description="Filter by estimation status, e.g. 'completed', 'in_progress', 'approved'.",
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return.",
    )


class SearchEstimationHistoryTool(BaseTool):
    name: str = "Search Estimation History"
    description: str = (
        "Search past estimations in PostgreSQL for historical reference. "
        "Filter by team, project, or status to find similar past projects, "
        "durations, and patterns. Useful for validating proposals against real data."
    )
    args_schema: Type[BaseModel] = SearchHistoryInput

    def _run(
        self,
        team_id: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> str:
        try:
            conn = _get_connection()
            cur = conn.cursor()

            conditions = []
            params: list = []

            if team_id:
                conditions.append("team_id = %s::uuid")
                params.append(team_id)
            if project_id:
                conditions.append("project_id = %s::uuid")
                params.append(project_id)
            if status:
                conditions.append("status = %s")
                params.append(status)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit)

            cur.execute(
                f"SELECT id, project_id, team_id, phase, status, data, created_at FROM estimator.estimation_history {where} ORDER BY created_at DESC LIMIT %s",
                params,
            )

            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                return "No estimation history found matching the criteria."

            results = [
                {
                    "id": str(row[0]),
                    "project_id": str(row[1]),
                    "team_id": str(row[2]),
                    "phase": row[3],
                    "status": row[4],
                    "data": row[5],
                    "created_at": row[6].isoformat(),
                }
                for row in rows
            ]
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error searching history: {e}"


# --- Patterns Tool (Agent 2 & 3: Analyst & Architect) ---


class SearchPatternsInput(BaseModel):
    """Input for searching design patterns."""

    pattern_name: str | None = Field(
        default=None,
        description="Exact or partial pattern name to search for, e.g. 'microservices', 'react-spa'.",
    )
    search_text: str | None = Field(
        default=None,
        description="Free-text search across pattern names and descriptions.",
    )


class SearchPatternsTool(BaseTool):
    name: str = "Search Design Patterns"
    description: str = (
        "Search the PostgreSQL patterns database for reusable framework and design patterns. "
        "Returns pattern data including technology stacks, typical timelines, and best practices. "
        "Use exact name or free-text search."
    )
    args_schema: Type[BaseModel] = SearchPatternsInput

    def _run(
        self,
        pattern_name: str | None = None,
        search_text: str | None = None,
    ) -> str:
        try:
            conn = _get_connection()
            cur = conn.cursor()

            if pattern_name:
                cur.execute(
                    "SELECT id, pattern_name, description, pattern_data FROM estimator.patterns WHERE pattern_name ILIKE %s ORDER BY pattern_name LIMIT 20",
                    (f"%{pattern_name}%",),
                )
            elif search_text:
                cur.execute(
                    "SELECT id, pattern_name, description, pattern_data FROM estimator.patterns"  # noqa: E501
                    " WHERE pattern_name ILIKE %s OR description ILIKE %s ORDER BY pattern_name LIMIT 20",
                    (f"%{search_text}%", f"%{search_text}%"),
                )
            else:
                cur.execute("SELECT id, pattern_name, description, pattern_data FROM estimator.patterns ORDER BY pattern_name LIMIT 20")

            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                return "No patterns found matching the criteria."

            results = [
                {
                    "id": str(row[0]),
                    "pattern_name": row[1],
                    "description": row[2],
                    "pattern_data": row[3],
                }
                for row in rows
            ]
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error searching patterns: {e}"


# --- Write Results Tool (Agent 3: Architect & Agent 4: Cost Specialist) ---


class SaveEstimationInput(BaseModel):
    """Input for saving estimation data."""

    estimation_id: str = Field(..., description="The estimation UUID to associate this data with.")
    project_id: str = Field(..., description="The project UUID.")
    team_id: str = Field(..., description="The team UUID.")
    user_id: str = Field(..., description="The user UUID.")
    phase: int = Field(..., description="The pipeline phase number (1-6).")
    status: str = Field(..., description="Status of this phase, e.g. 'completed', 'pending_approval'.")
    data: str = Field(
        ...,
        description="JSON string with the estimation results for this phase.",
    )


class SaveEstimationTool(BaseTool):
    name: str = "Save Estimation Results"
    description: str = (
        "Persist estimation results to PostgreSQL. "
        "Use this to save discovery findings, technical analysis, design blueprints, "
        "or any phase output for reporting (PDF, Excel) and future RAG retrieval."
    )
    args_schema: Type[BaseModel] = SaveEstimationInput

    def _run(
        self,
        estimation_id: str,
        project_id: str,
        team_id: str,
        user_id: str,
        phase: int,
        status: str,
        data: str,
    ) -> str:
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError:
            parsed_data = {"raw": data}

        try:
            conn = _get_connection()
            cur = conn.cursor()

            cur.execute(
                """INSERT INTO estimator.estimation_history
                   (project_id, team_id, user_id, phase, status, data)
                   VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s::jsonb)
                   RETURNING id""",
                (project_id, team_id, user_id, phase, status, json.dumps(parsed_data)),
            )

            row_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            return f"Estimation data saved successfully. Record ID: {row_id}"
        except Exception as e:
            return f"Error saving estimation: {e}"


# --- Financial Scenarios Tool (Agent 4: Cost Specialist) ---


class SaveFinancialScenarioInput(BaseModel):
    """Input for saving a financial scenario."""

    estimation_id: str = Field(..., description="The estimation UUID this scenario belongs to.")
    scenario_type: str = Field(
        ...,
        description="Type of scenario: 'human-only', 'ai-only', or 'hybrid'.",
    )
    costs: str = Field(..., description="JSON string with cost breakdown (labor, infrastructure, licensing, etc.).")
    timeline: str = Field(..., description="JSON string with timeline breakdown (phases, milestones, durations).")
    risks: str = Field(..., description="JSON string with risk assessment (probability, impact, mitigation).")


class SaveFinancialScenarioTool(BaseTool):
    name: str = "Save Financial Scenario"
    description: str = (
        "Save a cost scenario (human-only, ai-only, or hybrid) to PostgreSQL. Each scenario includes detailed cost breakdown, timeline, and risk analysis."
    )
    args_schema: Type[BaseModel] = SaveFinancialScenarioInput

    def _run(
        self,
        estimation_id: str,
        scenario_type: str,
        costs: str,
        timeline: str,
        risks: str,
    ) -> str:
        def _parse(val: str) -> dict:
            try:
                return json.loads(val) if isinstance(val, str) else val
            except json.JSONDecodeError:
                return {"raw": val}

        try:
            conn = _get_connection()
            cur = conn.cursor()

            cur.execute(
                """INSERT INTO estimator.financial_scenarios
                   (estimation_id, scenario_type, costs, timeline, risks)
                   VALUES (%s::uuid, %s, %s::jsonb, %s::jsonb, %s::jsonb)
                   RETURNING id""",
                (
                    estimation_id,
                    scenario_type,
                    json.dumps(_parse(costs)),
                    json.dumps(_parse(timeline)),
                    json.dumps(_parse(risks)),
                ),
            )

            row_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            return f"Financial scenario '{scenario_type}' saved. Record ID: {row_id}"
        except Exception as e:
            return f"Error saving financial scenario: {e}"
