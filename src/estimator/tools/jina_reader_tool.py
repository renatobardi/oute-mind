"""Jina Reader Tool for CrewAI agents.

Provides optimized web page reading via the self-hosted Jina Reader service.
Converts web pages to clean markdown, stripping ads, navigation, and boilerplate.
Used primarily by Agent 2 (Technical Research Analyst) for reading official documentation.
"""

import os
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JinaReaderInput(BaseModel):
    """Input for reading a web page via Jina Reader."""

    url: str = Field(
        ...,
        description="The full URL of the web page to read, e.g. 'https://docs.python.org/3/library/asyncio.html'.",
    )


class JinaReaderTool(BaseTool):
    name: str = "Read Web Page (Jina Reader)"
    description: str = (
        "Read and extract clean content from any web page using the Jina Reader service. "
        "Converts web pages to clean markdown text, removing ads, navigation, and boilerplate. "
        "Use this to read official documentation, technical blogs, API references, "
        "and framework guides. Returns the main content in a structured format."
    )
    args_schema: Type[BaseModel] = JinaReaderInput

    def _run(self, url: str) -> str:
        jina_host = os.getenv("JINA_READER_HOST", "jina-reader")
        jina_port = os.getenv("JINA_READER_PORT", "3000")
        jina_base = f"http://{jina_host}:{jina_port}"

        try:
            response = requests.get(
                jina_base,
                params={"url": url},
                timeout=30,
            )
            response.raise_for_status()
            content = response.text

            if not content or len(content.strip()) < 50:
                return f"Page at '{url}' returned very little content. It may require JavaScript rendering."

            # Truncate very long pages to avoid overwhelming the LLM context
            max_chars = 15000
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n... [Content truncated at {max_chars} characters]"

            return content
        except requests.exceptions.Timeout:
            return f"Timeout reading '{url}'. The page took too long to respond."
        except requests.exceptions.ConnectionError:
            return f"Could not connect to Jina Reader at {jina_base}. Ensure the service is running."
        except requests.exceptions.HTTPError as e:
            return f"HTTP error reading '{url}': {e}"
        except Exception as e:
            return f"Error reading '{url}': {e}"
