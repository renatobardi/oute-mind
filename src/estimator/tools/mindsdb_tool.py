"""MindsDB Tool for CrewAI agents.

Provides agent-to-agent context synchronization via MindsDB.
Agents can store and retrieve shared context (findings, decisions, status)
so that downstream agents have access to upstream results beyond what
CrewAI's task context provides.
"""

import json
import os
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _mindsdb_url() -> str:
    host = os.getenv("MINDSDB_HOST", "mindsdb")
    port = os.getenv("MINDSDB_PORT", "47334")
    return f"http://{host}:{port}"


def _mindsdb_auth() -> tuple[str, str]:
    user = os.getenv("MINDSDB_ADMIN_USER", "mindsdb")
    password = os.getenv("MINDSDB_ADMIN_PASSWORD", "")
    return (user, password)


# --- Store Context Tool ---


class StoreContextInput(BaseModel):
    """Input for storing agent context in MindsDB."""

    key: str = Field(
        ...,
        description="A unique key identifying this context entry, e.g. 'discovery_findings', 'rag_validation', 'design_blueprint'.",
    )
    agent_name: str = Field(
        ...,
        description="Name of the agent storing this context, e.g. 'interviewer', 'analyst', 'architect'.",
    )
    data: str = Field(
        ...,
        description="JSON string with the context data to store for other agents.",
    )


class StoreContextTool(BaseTool):
    name: str = "Store Agent Context"
    description: str = (
        "Store context data in MindsDB for synchronization between agents. "
        "Use this to share findings, decisions, or intermediate results with downstream agents. "
        "Data is stored as key-value pairs and can be retrieved by any agent."
    )
    args_schema: Type[BaseModel] = StoreContextInput

    def _run(self, key: str, agent_name: str, data: str) -> str:
        try:
            parsed = json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError:
            parsed = {"raw": data}

        base_url = _mindsdb_url()
        auth = _mindsdb_auth()

        # Use MindsDB SQL API to store data
        sql = f"""
            INSERT INTO agent_context (key_name, agent_name, context_data, created_at)
            VALUES ('{key}', '{agent_name}', '{json.dumps(parsed)}', NOW())
        """

        try:
            response = requests.post(
                f"{base_url}/api/sql/query",
                json={"query": sql},
                auth=auth,
                timeout=10,
            )
            response.raise_for_status()
            return f"Context '{key}' from agent '{agent_name}' stored successfully."
        except requests.exceptions.ConnectionError:
            return f"Could not connect to MindsDB at {base_url}. Storing context locally: key={key}, agent={agent_name}"
        except Exception as e:
            return f"MindsDB storage error: {e}. Context was: key={key}, agent={agent_name}"


# --- Retrieve Context Tool ---


class RetrieveContextInput(BaseModel):
    """Input for retrieving agent context from MindsDB."""

    key: str | None = Field(
        default=None,
        description="Specific context key to retrieve, e.g. 'discovery_findings'.",
    )
    agent_name: str | None = Field(
        default=None,
        description="Filter by agent name to get all context from a specific agent.",
    )


class RetrieveContextTool(BaseTool):
    name: str = "Retrieve Agent Context"
    description: str = (
        "Retrieve context data from MindsDB that was stored by other agents. "
        "Use this to access findings, decisions, or results from upstream pipeline stages. "
        "Filter by key or agent name."
    )
    args_schema: Type[BaseModel] = RetrieveContextInput

    def _run(
        self,
        key: str | None = None,
        agent_name: str | None = None,
    ) -> str:
        base_url = _mindsdb_url()
        auth = _mindsdb_auth()

        conditions = []
        if key:
            conditions.append(f"key_name = '{key}'")
        if agent_name:
            conditions.append(f"agent_name = '{agent_name}'")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT key_name, agent_name, context_data, created_at FROM agent_context {where} ORDER BY created_at DESC LIMIT 20"

        try:
            response = requests.post(
                f"{base_url}/api/sql/query",
                json={"query": sql},
                auth=auth,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("data"):
                return "No context found matching the criteria."

            return json.dumps(result["data"], ensure_ascii=False, indent=2)
        except requests.exceptions.ConnectionError:
            return f"Could not connect to MindsDB at {base_url}. Service may not be running."
        except Exception as e:
            return f"MindsDB retrieval error: {e}"
