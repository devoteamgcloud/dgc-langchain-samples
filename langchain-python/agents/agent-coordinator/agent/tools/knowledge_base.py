"""Knowledge base tool."""
import os

import google.auth.transport.requests
import google.oauth2.id_token
from langchain_core.pydantic_v1 import BaseModel, Field
from langserve import RemoteRunnable


class KnowledgeBaseInput(BaseModel):
    """Knowledge base input."""

    query: str = Field(
        description="query to the knowledge base",
    )


def knowledge_base_tool(authorization_token: str):
    """Knowledge base tool."""

    def _wrapper(query: str):
        cloud_run_id_token = None
        agent_knowledge_base_url = os.environ.get("_AGENT_KNOWLEDGE_BASE_URL")
        if agent_knowledge_base_url:
            auth_req = google.auth.transport.requests.Request()
            cloud_run_id_token = google.oauth2.id_token.fetch_id_token(
                auth_req,
                agent_knowledge_base_url,
            )

        chat = RemoteRunnable(
            agent_knowledge_base_url or "http://localhost:8081/",
            headers={
                "Authorization": (
                    f"Bearer {cloud_run_id_token}"
                    if cloud_run_id_token
                    else authorization_token
                ),
            },
        )
        answer = chat.invoke(
            {
                "message": f"{query}",
            },
        )["output"]
        return answer

    return _wrapper
